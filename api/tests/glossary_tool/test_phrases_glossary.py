import sys
import os
import pprint

# Add the directory containing glossary_service to the Python path
# This assumes the script is run from the parent directory of 'glossary_service'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now, import the class
from api.tools.glossary_service.glossary_service import GlossaryService

def run_glossary_service_tests():
    """Runs a suite of tests for the GlossaryService class."""
    
    print("="*80)
    print("🧪  STARTING GLOSSARY SERVICE TEST SUITE 🧪")
    print("="*80)
    
    # 1. Initialization Test
    print("\n[Phase 1: Service Initialization]")
    try:
        # Ensure your 11 .json files are in a folder named 'glossaries'
        # inside the 'glossary_service' directory.
        glossary_service = GlossaryService(glossaries_dir='api/tools/glossary_service/glossaries')
        print("✅ Service initialized successfully.")
        print(f"   - Indexed {len(glossary_service.all_known_phrases)} unique phrases and aliases.")
    except Exception as e:
        print(f"❌ CRITICAL: Service failed to initialize: {e}")
        return

    # 2. Alias Generation & Indexing Test
    # We test this implicitly by searching for aliases of a known complex term.
    print("\n[Phase 2: Alias Generation & Indexing Test]")
    term_to_check = "Pertussis (Whooping Cough)"
    expected_aliases = ["pertussis (whooping cough)", "pertussis", "whooping cough"]
    all_aliases_found = True
    for alias in expected_aliases:
        if alias not in glossary_service.phrase_index:
            print(f"❌ FAILED: Alias '{alias}' for term '{term_to_check}' was not found in the index.")
            all_aliases_found = False
    if all_aliases_found:
        print(f"✅ SUCCESS: All expected aliases for '{term_to_check}' are correctly indexed.")


    # 3. Core Functionality Test: Finding phrases in text
    print("\n[Phase 3: Core Functionality - Finding Phrases in Text]")
    test_text = """Rationale
Trauma systems have become the standard of care in high‐income countries, but remain uncommon in low‐ and middle‐income countries. High‐quality evidence of effectiveness is needed to advocate for the development of trauma systems in low‐ and middle‐income countries, where the burden of injury is highest.

Objectives
To assess the benefits and harms of organised trauma systems and designated trauma centres compared with usual care in injured patients.

Search methods
We searched CENTRAL, MEDLINE, Embase, ClinicalTrials.gov, and WHO ICTRP on 16 December 2023. We also searched grey literature, checked reference lists of included studies, and contacted the authors of relevant studies.

Eligibility criteria
We included randomised controlled trials, non‐randomised trials, controlled before‐after studies, and interrupted time series studies comparing organised trauma systems or designated trauma centres with usual care. We planned to include patients who had had major trauma (i.e. Injury Severity Score greater than 15), but made a post‐hoc decision to include patients regardless of injury severity. Studies were considered for inclusion regardless of date, language, or publication status.

Outcomes
The critical outcomes were patient outcomes (such as mortality, survival, and recovery), and adverse effects. Important outcomes were utilisation and access to trauma care services, quality of care provided, equity, and knowledge about trauma care services. Studies only reported patient outcomes (mortality, survival); there were no reports on adverse effects, utilisation and access to services, quality of care, equity, and knowledge about trauma care services.

Risk of bias
We used the Cochrane RoB 1 tool and guidance from the Cochrane Effective Practice and Organisation of Care (EPOC) group to evaluate individual studies.

Synthesis methods
Two review authors independently selected studies for inclusion, extracted data, and assessed risk of bias and certainty of evidence using GRADE. We could not perform a meta‐analysis due to substantial clinical heterogeneity across studies. We re‐analysed data from individual studies so they could be presented in a standardised format as relative effect, change in level, and change in slope. We summarised findings using a narrative synthesis."""
    print(f"   - Analyzing text: \"{test_text}\"")
    
    report = glossary_service.find_and_define_phrases_in_text(test_text)
    
    print(f"   - Report generated. Found {len(report)} distinct complex phrases.")
    pprint.pprint(report)
    
    expected_phrases = ["clinical trial", "adverse effects", "oral poliovirus (opv)"]
    for phrase in expected_phrases:
        if phrase in report:
            print(f"   ✅ Found expected phrase: '{phrase}'")
        else:
            print(f"   ❌ FAILED to find expected phrase: '{phrase}'")


    # 4. Longest-Match-First Test (Handling Overlaps)
    print("\n[Phase 4: Overlap Test - Ensuring Longest Match Priority]")
    overlap_text = "This chronic disease is not just any disease."
    print(f"   - Analyzing text: \"{overlap_text}\"")
    
    overlap_report = glossary_service.find_and_define_phrases_in_text(overlap_text)
    
    print("   - Results:")
    pprint.pprint(overlap_report)

    if "chronic disease" in overlap_report:
        print("   ✅ SUCCESS: Correctly identified the longer phrase 'chronic disease'.")
    else:
        print("   ❌ FAILED: Did not identify 'chronic disease'.")

    if "disease" in overlap_report and "chronic disease" in overlap_report:
         print("   ⚠️ WARNING: Found 'disease' as a separate term, which might be okay but shows the importance of the replacement logic.")
    elif "disease" not in overlap_report:
        print("   ✅ SUCCESS: Correctly ignored the shorter sub-phrase 'disease' after finding the longer one.")


    # 5. Case-Insensitivity Test
    print("\n[Phase 5: Case-Insensitivity Test]")
    case_test_text = "The study on MYOCARDIAL INFARCTION showed clear results."
    print(f"   - Analyzing text: \"{case_test_text}\"")

    case_report = glossary_service.find_and_define_phrases_in_text(case_test_text)
    
    print("   - Results:")
    pprint.pprint(case_report)

    if "myocardial infarction" in case_report:
        print("   ✅ SUCCESS: Correctly identified 'myocardial infarction' regardless of case.")
    else:
        print("   ❌ FAILED: The search is case-sensitive.")

    print("\n" + "="*80)
    print("🎉  TEST SUITE COMPLETED 🎉")
    print("="*80)


if __name__ == "__main__":
    # To run this test:
    # 1. Make sure you have a parent directory.
    # 2. Inside, create the 'glossary_service' directory.
    # 3. Put your 'glossary_service.py' and the 'glossaries' folder (with the 11 JSONs) inside 'glossary_service'.
    # 4. Put this 'test_glossary_service.py' file in the parent directory.
    # 5. Run 'python test_glossary_service.py' from the parent directory.
    run_glossary_service_tests()