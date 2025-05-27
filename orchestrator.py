import yaml
import pathlib
import os
import json
import sys
import re
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime # For timestamped output files

# ── Setup ──────────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set", file=sys.stderr); sys.exit(1)

config_path = "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    model_config = yaml.safe_load(f) or {}
    model_name = model_config.get("model")
if not model_name:
    print("Error: 'model' key missing in config.yaml", file=sys.stderr); sys.exit(1)

client = OpenAI(api_key=api_key)
print(f"Using model: {model_name}")

options_path = "options.yaml"
with open(options_path, "r", encoding="utf-8") as f:
    case_cfg = yaml.safe_load(f) or {}
CASE_PROMPT = case_cfg.get("prompt", "Default case prompt if not found.") # Added .get for robustness
ORIG_OPTIONS = case_cfg.get("options", []) # Added .get for robustness

# MODIFIED: Initialize OPTIONS directly from ORIG_OPTIONS
# Make a copy if you anticipate modifying OPTIONS independently of ORIG_OPTIONS later,
# though in this simplified flow, direct assignment is fine.
OPTIONS = list(ORIG_OPTIONS) # Ensures OPTIONS is a distinct list based on original options

if not CASE_PROMPT or not OPTIONS:
    print(f"Error: 'prompt' or 'options' missing or empty in {options_path}. Exiting.", file=sys.stderr)
    sys.exit(1)

# ── Helpers ───────────────────────────────────────────────────────────────
# load_persona function remains the same as previously modified
def load_persona(path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if 'name' in data and 'principle' in data: # Basic check
            return data
    except Exception as e:
        print(f"Error loading persona {path.name}: {e}", file=sys.stderr)
    return None

# speak function remains the same as previously modified (with full persona details)
def speak(pname, pdet, prompt, summary=False):
    system_msg = ""
    if summary:
        system_msg = "You are a neutral summariser tasked with the following."
    else:
        if not pdet or 'name' not in pdet:
            system_msg = f"You are an AI assistant. Please respond to the user's prompt."
            print(f"Warning: Insufficient persona details for {pname}. Using generic prompt.", file=sys.stderr)
        else:
            persona_name_from_yaml = pdet.get('name', pname)
            system_msg_parts = [
                f"You are to fully embody the persona of '{persona_name_from_yaml}'. "
                f"Adhere strictly to ALL the following characteristics in your reasoning, arguments, communication style, and decisions. "
                f"Your responses must be consistent with every aspect of this persona definition:\n"
            ]
            for key, value in pdet.items():
                formatted_key = key.replace('_', ' ').capitalize()
                system_msg_parts.append(f"\n## {formatted_key}:\n")
                if isinstance(value, list):
                    if not value: system_msg_parts.append("- (No specific details provided for this item)\n")
                    for item in value: system_msg_parts.append(f"- {item}\n")
                elif isinstance(value, dict):
                    if not value: system_msg_parts.append("- (No specific details provided for this item)\n")
                    for sub_key, sub_value in value.items():
                        formatted_sub_key = sub_key.replace('_', ' ').capitalize()
                        system_msg_parts.append(f"  - **{formatted_sub_key}**: ")
                        if isinstance(sub_value, list):
                            if not sub_value: system_msg_parts.append("(empty list)\n"); continue
                            system_msg_parts.append("\n")
                            for sv_item in sub_value: system_msg_parts.append(f"    - {sv_item}\n")
                        else: system_msg_parts.append(f"{sub_value}\n")
                else: system_msg_parts.append(f"{value}\n")
            system_msg_parts.append(
                "\nMaintain this persona consistently and rigorously. "
                "Your primary goal is to reflect all these defined characteristics in your output. "
                "Do not break character."
            )
            system_msg = "".join(system_msg_parts)
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role":"system","content":system_msg}, {"role":"user","content":prompt}])
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error for {pname if not summary else 'Summarizer'}: {e}", file=sys.stderr)
        return "[API error]"

# format_debate_to_text function remains the same
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
    if 'executive_summary' in debate:
        out.append("\n\n=== EXECUTIVE SUMMARY ===")
        out.append(debate['executive_summary'])
    return "\n".join(out)

if __name__ == "__main__":
    # Initialize debate dictionary with prompt and options directly.
    # The global OPTIONS is already set from ORIG_OPTIONS.
    debate = {"case_details":{"prompt": CASE_PROMPT, "options": list(OPTIONS)}, "participants":{}}

    personas_dir = pathlib.Path("personas")
    pfiles = list(personas_dir.glob("*.yaml"))
    if not pfiles:
        print(f"Error: No persona YAML files found in directory '{personas_dir.resolve()}'. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    for pf in pfiles:
        pdata = load_persona(pf)
        if not pdata: continue
        pname = pdata['name']
        
        if pname in debate['participants']:
            print(f"Warning: Persona name '{pname}' from {pf.name} conflicts. Skipping.", file=sys.stderr)
            continue

        print(f"Loading persona: {pname}")
        opening_prompt = (
            f"You are about to participate in an ethical debate. This is the scenario and your task for the opening statement:\n\n"
            f"{CASE_PROMPT}\n\n"
            f"The policy options under consideration are:\n" + 
            "\n".join([f"- {opt}" for opt in OPTIONS]) + "\n\n"
            f"Based on your detailed persona characteristics, provide your opening statement. "
            f"Clearly state your initial position and the primary reasons derived from your persona's framework."
        )
        opening = speak(pname, pdata, opening_prompt)
        # MODIFIED: Removed 'proposed_options_raw'
        debate['participants'][pname] = {"persona_definition":pdata,
                                         "opening":opening,
                                         "rebuttal":"",
                                         "vote_justification_and_vote":"",
                                         "final_vote":""}

    if not debate['participants']:
        print("Error: No personas were successfully loaded. Exiting.", file=sys.stderr)
        sys.exit(1)

    # REMOVED: Entire "Round 0b - Organic Option Generation" if/else block.
    # The `debate['case_details']['options']` is already correctly set from the global `OPTIONS`
    # during the initialization of the `debate` dictionary.
    # We can confirm the options being used:
    print(f"Debate will proceed with the following predefined options: {debate['case_details']['options']}")
    if not debate['case_details']['options']: # Should not happen if options_path check above is robust
        print("Error: No options available for the debate. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Rebuttals
    print("Starting Rebuttals Round...")
    # ... (Rebuttal logic remains the same, it uses debate['case_details']['options']) ...
    for pname_speaker, pdata_speaker_dict in debate['participants'].items():
        persona_definition_speaker = pdata_speaker_dict['persona_definition']
        other_openings_parts = []
        for pname_other, pdata_other_dict in debate['participants'].items():
            if pname_other != pname_speaker:
                other_openings_parts.append(f"--- Opening Statement from {pname_other} ---\n{pdata_other_dict['opening']}\n--- End of Statement from {pname_other} ---")
        others_text = "\n\n".join(other_openings_parts) if other_openings_parts else "No other participants' statements to rebut."

        rebuttal_prompt = (
            f"The following are the opening statements from other participants in the debate:\n\n"
            f"{others_text}\n\n"
            f"The policy options currently under consideration are:\n"
            + "\n".join([f"- {opt}" for opt in debate['case_details']['options']]) + "\n\n"
            f"Based on your detailed persona characteristics and the opening statements provided, "
            f"formulate your rebuttal. You may critique others' positions, defend your own, "
            f"and clarify how your persona's principles apply to the arguments made."
        )
        pdata_speaker_dict['rebuttal'] = speak(pname_speaker, persona_definition_speaker, rebuttal_prompt)
        print(f"Rebuttal by {pname_speaker} completed.")

    # Construct full transcript for voting context
    # ... (Transcript construction logic remains the same) ...
    transcript_parts = []
    for name, data in debate['participants'].items():
        transcript_parts.append(f"=== Opening Statement by {name} ===\n{data['opening']}")
        if data['rebuttal']: transcript_parts.append(f"=== Rebuttal by {name} ===\n{data['rebuttal']}")
    full_transcript_for_vote = "\n\n".join(transcript_parts)
    
    options_block_for_vote = "\n".join([f"- {idx+1}. {opt}" for idx, opt in enumerate(debate['case_details']['options'])])


    # Votes
    print("Starting Voting Round...")
    # ... (Voting logic remains the same, it uses options_block_for_vote derived from debate['case_details']['options']) ...
    for pname, pdata_dict in debate['participants'].items():
        persona_definition = pdata_dict['persona_definition']
        vote_prompt = (
            f"The full debate transcript so far is:\n\n"
            f"{full_transcript_for_vote}\n\n"
            f"The final list of policy options to choose from is:\n"
            f"{options_block_for_vote}\n\n"
            f"Instructions for Voting:\n"
            f"1. Based on your complete persona definition and your analysis of the debate, "
            f"choose the single best option from the list above that most aligns with your persona's ethical framework and decision criteria.\n"
            f"2. First, clearly state your chosen option *exactly* as it appears in the list (including the number if present), enclosed within <vote> tags. For example: <vote>1. Option Text Here</vote>.\n"
            f"3. After the <vote> tag line, provide a detailed justification for your choice, explaining how it connects to your persona's principles, values, and your assessment of the arguments made during the debate."
        )
        vote_output = speak(pname, persona_definition, vote_prompt)
        pdata_dict['vote_justification_and_vote'] = vote_output
        vote_match = re.search(r"<vote>(.*?)</vote>", vote_output, re.IGNORECASE | re.DOTALL)
        parsed_vote = "Could not parse vote"
        if vote_match:
            extracted_option_text = vote_match.group(1).strip()
            found_match = False
            for official_opt in debate['case_details']['options']:
                if official_opt.lower() in extracted_option_text.lower() or extracted_option_text.lower() == official_opt.lower():
                    parsed_vote = official_opt
                    found_match = True
                    break
            if not found_match:
                print(f"Warning: Extracted vote '{extracted_option_text}' for {pname} does not directly match official options. Storing as is.", file=sys.stderr)
                parsed_vote = f"Potentially unaligned vote: {extracted_option_text}"
        else:
             print(f"Warning: Could not find <vote> tag in output for {pname}. Vote parsing failed.", file=sys.stderr)
        pdata_dict['final_vote'] = parsed_vote
        print(f"Vote by {pname}: {parsed_vote}")

    # Summary
    print("Generating Main Summary...")
    # ... (Main summary logic remains the same) ...
    summary_prompt_parts = [
        "Objectively summarise the debate. For each participant, include:\n"
        "- Their final chosen policy option (as parsed).\n"
        "- A concise summary of their justification for that choice, linking it to their core ethical principles.\n\n"
        "After summarizing each participant, provide a final vote tally for each policy option.\n\n"
        "**If there was any divergence in the final votes (i.e., not unanimous), specifically identify the participant(s) who voted differently. "
        "Analyze their justification to explain the core reasons for their divergence compared to the majority (or other factions), referencing their stated ethical framework and how it led them to a different conclusion.**\n\n"
        "Participant contributions and votes:\n"
    ]
    for name, data in debate['participants'].items():
        summary_prompt_parts.append(
            f"--- Participant: {name} ---\n"
            f"Final Vote Parsed: {data['final_vote']}\n"
            f"Full Justification Provided:\n{data['vote_justification_and_vote']}\n" 
            f"--- End {name} ---"
        )
    main_summary_prompt = "\n".join(summary_prompt_parts)
    debate['summary'] = speak("MainSummarizer", {}, main_summary_prompt, summary=True)
    print("Main Summary generated.")

    # Executive Summary
    print("Generating Executive Summary...")
    # ... (Executive summary logic remains the same) ...
    exec_summary_criteria = (
        "Write an executive summary (strictly 300 words or less) of the preceding debate. Highlight the following aspects using short, punchy bullet points under clear headings:\n"
        "• The core ethical problem and the policy options considered.\n"
        "• Overall vote tally and the most chosen option(s).\n"
        "• Key points of consensus or significant agreement across different personas.\n"
        "• Major points of disagreement or ethical clashes, and briefly why they arose based on differing persona frameworks.\n"
        "• Any particularly novel, surprising, or influential arguments, or unique perspectives offered by specific personas.\n"
        "• If applicable, any unresolved questions or clear next steps suggested by the debate's outcome.\n"
        "Focus on the essence of the debate and its outcomes from a high level."
    )
    exec_summary_body_parts = ["Debate context for Executive Summary:\n"]
    exec_summary_body_parts.append(f"Case Prompt: {debate['case_details']['prompt']}")
    exec_summary_body_parts.append("Options Considered: " + ", ".join(debate['case_details']['options']))
    exec_summary_body_parts.append("\nParticipant votes and justifications:\n")
    for name, data in debate['participants'].items():
        exec_summary_body_parts.append(f"Participant: {name}\nVoted for: {data['final_vote']}\n")
    exec_summary_body_parts.append(f"\nFull Debate Summary for context:\n{debate['summary']}")
    full_prompt_for_exec_summary = "\n".join(exec_summary_body_parts) + f"\n\nTask:\n{exec_summary_criteria}"
    debate['executive_summary'] = speak("ExecutiveSummarizer", {}, full_prompt_for_exec_summary, summary=True)
    print("Executive Summary generated.")

    # Save outputs
    # ... (Saving logic with timestamped filenames remains the same) ...
    output_dir = pathlib.Path("debate_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"debate_{timestamp_str}"
    json_output_path = output_dir / f"{base_filename}_output.json"
    report_output_path = output_dir / f"{base_filename}_report.txt"
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(debate, f, indent=2, ensure_ascii=False)
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(format_debate_to_text(debate))
    print(f"Debate complete. Outputs saved to '{json_output_path}' and '{report_output_path}'")
