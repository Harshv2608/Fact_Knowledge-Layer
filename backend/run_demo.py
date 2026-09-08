import os
import json
import asyncio

if 'MOCK_LLM' in os.environ:
    del os.environ['MOCK_LLM']
# Use environment variable for API key instead of hardcoding
# Ensure GEMINI_API_KEY is set in your environment before running

from app.extraction.llm_extractor import extract_facts_from_chunk
from app.reasoning.comparator import compare_facts

async def main():
    print('--- CASE 1 & 3 ---')
    t1 = 'Although real gross domestic product (GDP) growth moderated to 6.5 per cent in 2024-25, India remained the fastest growing large economy. Headline inflation moderated to an average of 4.6 per cent during 2024-25 from 5.4 per cent in the previous year.'
    f1 = extract_facts_from_chunk(t1, 'RBI Annual Report')
    print('RBI facts:', json.dumps(f1, indent=2))
    
    t2 = 'India’s real GDP grew by 6.5 percent in FY2024/25. Headline inflation has declined to 1.5 percent in September 2025, down from 4.6 percent (FY2024/25 average).'
    f2 = extract_facts_from_chunk(t2, 'IMF Article IV')
    print('IMF facts:', json.dumps(f2, indent=2))
    
    t3 = 'Retail headline inflation, as measured by the change in the Consumer Price Index (CPI), has softened from 5.4 per cent in FY24 to 4.9 per cent in April - December 2024.'
    f3 = extract_facts_from_chunk(t3, 'Economic Survey')
    print('ES facts:', json.dumps(f3, indent=2))
    
    all_facts = f1 + f2 + f3
    for i, f in enumerate(all_facts): f['id'] = i + 1
    
    print('Comparing...')
    rels = await compare_facts(all_facts)
    print('Relationships:', json.dumps(rels, indent=2))
    
    print('--- CASE 4 ---')
    t4 = 'Table 1. Balance of payments (in billions of U.S. dollars). Foreign direct investment, net ('-' signifies inflow) -1.0'
    f4 = extract_facts_from_chunk(t4, 'IMF Article IV')
    print('Tricky facts:', json.dumps(f4, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
