import yaml
import pathlib
import os
import json
import sys
import re
from openai import OpenAI
from dotenv import load_dotenv

"""
ORCHESTRATOR – v2
Adds an optional “organic options” phase (Round 0b) where personas propose
management options that are deduplicated by a helper agent.
"""
GENERATE_ORGANIC_OPTIONS = False
MAX_OPTIONS_AFTER_DEDUP = 4

# ── Setup ──────────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set"); sys.exit(1)

config_path = "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    model_name = (yaml.safe_load(f) or {}).get("model")
if not model_name:
    print("Error: 'model' key missing in config.yaml"); sys.exit(1)

client = OpenAI(api_key=api_key)
print(f"Using model: {model_name}")

options_path = "options.yaml"
with open(options_path, "r", encoding="utf-8") as f:
    case_cfg = yaml.safe_load(f) or {}
CASE_PROMPT = case_cfg["prompt"]
ORIG_OPTIONS = case_cfg["options"]
OPTIONS = ORIG_OPTIONS if not GENERATE_ORGANIC_OPTIONS else []

# ── Helpers ───────────────────────────────────────────────────────────────
def load_persona(path):
    try:  # <--- Indentation here must be standard spaces (e.g., 4 spaces)
        # Ensure this line's indentation is also standard spaces (e.g., 8 spaces)
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if 'name' in data and 'principle' in data:
            return data
    except Exception as e: # <--- Indentation here must match the 'try' (e.g., 4 spaces)
        print(f"Skip {path.name}: {e}")
    return None # <--- Indentation here must match the 'try' (e.g., 4 spaces)


def speak(pname, pdet, prompt, summary=False):
    system_msg = ("You are a neutral summariser." if summary else
                  f"You are the {pname} ethicist ({pdet['name']}). "
                  f"Principle: {pdet['principle']}. "
                  "Stay in character.")
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role":"system","content":system_msg},
                      {"role":"user","content":prompt}])
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error for {pname}: {e}")
        return "[API error]"

def format_debate_to_text(debate):
    out = ["--- DEBATE REPORT ---", "\n=== CASE DETAILS ===",
           f"Prompt: {debate['case_details']['prompt']}", "Options:"]
    out.extend(f"- {o}" for o in debate['case_details']['options'])
    out.append("\n\n=== PARTICIPANT CONTRIBUTIONS ===")
    for n,d in debate['participants'].items():
        out.extend([f"\n\n--- {n} ---","\n-- Opening --",d['opening'],
                    "\n-- Rebuttal --",d['rebuttal'],
                    "\n-- Vote & Justification --",d['vote_justification_and_vote']])
    out.append("\n\n=== SUMMARY ===")
    out.append(debate['summary'])
    return "\n".join(out)

if __name__ == "__main__":
    debate = {"case_details":{"prompt":CASE_PROMPT,"options":[]}, "participants":{}}

    personas_dir = pathlib.Path("personas")
    pfiles = list(personas_dir.glob("*.yaml"))
    for pf in pfiles:
        pdata = load_persona(pf)
        if not pdata: continue
        pname = pdata['name']
        opening = speak(pname, pdata, CASE_PROMPT)
        debate['participants'][pname] = {"persona_definition":pdata,
                                         "opening":opening,
                                         "rebuttal":"",
                                         "proposed_options_raw":"",
                                         "vote_justification_and_vote":"",
                                         "final_vote":""}

    # Round 0b
    if GENERATE_ORGANIC_OPTIONS:
        raw = []
        for pname,pdata in debate['participants'].items():
            pdef = pdata['persona_definition']
            oprompt = ("Based on the case details provided and your persona's ethical framework, propose up to two concrete *actions* or *decisions* that should be taken to address the core ethical conflict presented in the case. "
                       "Focus on specific interventions, resolutions, or definitive next steps, rather than general processes like 'discuss more' or 'gather information' unless such processes are the *only* ethically justifiable actions from your perspective. "
                       "Start each proposed option on a new line, prefixed with 'Option: '. Keep each option concise (e.g., maximum ~30 words).")
            txt = speak(pname, pdef, oprompt)
            pdata['proposed_options_raw'] = txt
            raw.extend(re.findall(r"^Option:\s*(.+)$", txt, flags=re.M))
        raw=[o.strip() for o in raw if o.strip()]
        if raw:
            dprompt = ("Deduplicate and return at most "
                       f"{MAX_OPTIONS_AFTER_DEDUP} options, each line prefixed '•'.\n"
                       + "\n".join("- "+o for o in raw))
            dedup = speak("Deduplicator", {}, dprompt, summary=True)
            OPTIONS = [l.lstrip('• ').strip() for l in dedup.splitlines() if l.startswith('•')]
        if not OPTIONS:
            OPTIONS = ORIG_OPTIONS
    else:
        OPTIONS = ORIG_OPTIONS
    debate['case_details']['options']=OPTIONS

    # Rebuttals
    for pname,pdata in debate['participants'].items():
        pdef=pdata['persona_definition']
        others="\n".join(f"--- {o} ---\n{debate['participants'][o]['opening']}"
                          for o in debate['participants'] if o!=pname)
        rprompt=(f"Rebut the following openings:\n{others}\nRespond as {pname}.")
        pdata['rebuttal']=speak(pname,pdef,rprompt)

    transcript="\n\n".join(f"=== {a} ===\nO:\n{d['opening']}\nR:\n{d['rebuttal']}"
                             for a,d in debate['participants'].items())
    opts_block="\n".join("- "+o for o in OPTIONS)

    # Votes
    for pname, pdata in debate['participants'].items():
        pdef = pdata['persona_definition']
        
        # --- MODIFIED PROMPT ---
        # Added explicit instructions for the <vote> tag format
        vprompt = (
            f"Debate transcript:\n{transcript}\n\n"
            f"Options:\n{opts_block}\n\n"
            f"Instructions:\n"
            f"1. Choose the single best option from the list above that aligns with your persona's ({pname}) ethical framework.\n"
            f"2. First, state your chosen option *exactly* as written in the list, enclosed within <vote> tags. For example: <vote>Option Text Here</vote>\n"
            f"3. After the <vote> line, provide your detailed justification, explaining why you chose this option based on your persona's principles and the debate transcript."
        )
        
        # Get the response from the AI
        vout = speak(pname, pdef, vprompt)
        pdata['vote_justification_and_vote'] = vout

        # --- MODIFIED PARSING LOGIC ---
        # Use regex to find the content within <vote>...</vote> tags
        vote_match = re.search(r"<vote>(.*?)</vote>", vout, re.IGNORECASE | re.DOTALL)
        
        parsed_vote = "Could not parse vote" # Default value
        if vote_match:
            extracted_option = vote_match.group(1).strip()
            # Validate if the extracted option is one of the official options
            if extracted_option in OPTIONS:
                parsed_vote = extracted_option
            else:
                # Log if the extracted text is not a valid option
                print(f"Warning: Extracted vote '{extracted_option}' for {pname} not in official options list.")
                parsed_vote = "Parsed vote not in options list" 
        else:
             print(f"Warning: Could not find <vote> tag in output for {pname}.")
             # Optional: You could try falling back to the old last-line method here,
             # or just accept that parsing failed.
             # Example fallback (uncomment if desired):
             # try:
             #    last_line = [l.strip() for l in vout.splitlines() if l.strip()][-1]
             #    if last_line in OPTIONS:
             #        parsed_vote = last_line
             #        print(f"Info: Using fallback (last line) vote for {pname}.")
             # except IndexError:
             #    pass # Keep as "Could not parse vote" if no lines found

        pdata['final_vote'] = parsed_vote

    # Summary (No changes needed here, but ensure it follows the modified # Votes section)
    sum_prompt="Summarise positions and votes objectively, including the final parsed vote for each participant."
    # Slightly modified sum_body to potentially include the parsed vote explicitly if needed, 
    # though the summarizer model should pick it up from the context.
    sum_body="\n\n".join(f"=== {n} ===\nVote Parsed: {d['final_vote']}\nFull Justification:\n{d['vote_justification_and_vote']}"
                           for n,d in debate['participants'].items())
    debate['summary']=speak("Summary",{},f"{sum_body}\n\n{sum_prompt}",summary=True)

    # Save (No changes needed here)
    # ... (rest of the script remains the same) ...

    # Summary
    sum_prompt = (
        "Summarise the final position and vote justification for each participant objectively. "
        "Identify the final vote tally for each option. "
        "**If there was any divergence in the final votes (i.e., not unanimous), specifically identify the participant(s) who voted differently and analyze their justification to explain the core reasons for their divergence compared to the majority, referencing their ethical framework.**"
    )
    sum_body="\n\n".join(f"=== {n} ===\n{d['vote_justification_and_vote']}"
                           for n,d in debate['participants'].items())
    debate['summary']=speak("Summary",{},f"{sum_body}\n\n{sum_prompt}",summary=True)
    # --- Executive Summary -----------------------------------------------
    exec_criteria = (
        "Write an executive summary (≤300 words) that highlights:\n"
        "• Points of consensus across personas\n"
        "• Sharp disagreements and why they arise\n"
        "• Any minority/out-lier views\n"
        "• The most novel or surprising arguments, citations or precedents\n"
        "• Unresolved questions and next-step suggestions\n"
        "Use short, punchy bullet-points grouped under clear headings."
    )

    exec_body = "\n\n".join(
        f"=== {name} ===\nVote: {d['final_vote']}\n{d['vote_justification_and_vote']}"
        for name, d in debate['participants'].items()
    )

    debate['executive_summary'] = speak(
        "Executive Editor",               # persona name
        {},                               # no persona definition needed
        f"{exec_body}\n\n{exec_criteria}",# full prompt
        summary=True                      # switches 'speak' into summariser mode
    )

    # Save
    with open("debate_output.json","w",encoding="utf-8") as f:
        json.dump(debate,f,indent=2,ensure_ascii=False)
    with open("debate_report.txt","w",encoding="utf-8") as f:
        f.write(format_debate_to_text(debate))
    print("Debate complete. See debate_output.json and debate_report.txt")
