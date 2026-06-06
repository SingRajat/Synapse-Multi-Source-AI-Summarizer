map_prompt = """Summarize the following text. Focus on the main ideas, key facts, and important insights.
Text:
{text}
Summary:"""
refine_prompt = """You have an existing summary and new information. Combine them into a single, improved summary. 
Remove redundancy and preserve all important details.
Existing Summary:
{existing_summary}
New Information:
{new_summary}
Refined Summary:"""