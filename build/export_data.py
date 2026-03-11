#!/usr/bin/env python3
"""
SpanishKB Study PWA — Data Export Script
Parses SpanishKB vault and exports data.json for the study app.

Exports four data types:
  1. words       — 5,000 frequency-ranked vocabulary from Vocabulario/*.md
  2. conjugations — verb conjugation cards from Verbos/*.md
  3. medicalVocab — medical vocabulary harvested from Verbos/ Medical Context sections
  4. medicalPhrases — clinical phrases harvested from Verbos/ Medical Context sections
"""

import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# PATHS
# ============================================================
VAULT_PATH = Path(r"C:\Users\stace\spaceport\SpanishKB")
VOCAB_PATH = VAULT_PATH / "Vocabulario"
VERBOS_PATH = VAULT_PATH / "Verbos"
MEDICO_PATH = VAULT_PATH / "Español Médico"
OUTPUT_PATH = Path(r"C:\Users\stace\spaceport\SpanishKB-Study\app\data.json")

# ============================================================
# 1. VOCABULARY EXPORT
# ============================================================
VOCAB_ROW = re.compile(
    r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\S+)\s*\|\s*(.+?)\s*\|$'
)

def parse_frontmatter(text):
    """Extract YAML frontmatter fields."""
    fm = {}
    if text.startswith('---'):
        end = text.find('---', 3)
        if end > 0:
            block = text[3:end]
            for line in block.strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    # Parse simple values
                    if val.isdigit():
                        fm[key] = int(val)
                    else:
                        fm[key] = val
    return fm

def export_vocabulary():
    """Parse all Vocabulario/*.md files into word objects."""
    words = []
    if not VOCAB_PATH.exists():
        print(f"  WARNING: {VOCAB_PATH} not found, skipping vocabulary")
        return words

    for md_file in sorted(VOCAB_PATH.glob("*.md")):
        text = md_file.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        tier = fm.get('tier', 1)

        for line in text.split('\n'):
            m = VOCAB_ROW.match(line)
            if m:
                rank = int(m.group(1))
                es = m.group(2).strip()
                en = m.group(3).strip()
                pos = m.group(4).strip()
                ex = m.group(5).strip()

                # Skip untranslated placeholders
                if en in ('—', '---', '-'):
                    continue

                words.append({
                    'rank': rank,
                    'es': es,
                    'en': en,
                    'type': pos,
                    'ex': ex,
                    'tier': tier
                })

    words.sort(key=lambda w: w['rank'])
    print(f"  Vocabulary: {len(words)} words exported")
    return words

# ============================================================
# 2. CONJUGATION EXPORT
# ============================================================
CONJ_TABLE_ROW = re.compile(
    r'^\|\s*(yo|tú|él/ella/Ud\.)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$'
)

TENSE_HEADER = re.compile(
    r'^###\s+(.+?)(?:\s*\((.+?)\))?\s*$'
)

TENSE_MAP = {
    'presente': 'presente',
    'present indicative': 'presente',
    'present': 'presente',
    'pretérito': 'pretérito',
    'preterite': 'pretérito',
    'imperfecto': 'imperfecto',
    'imperfect': 'imperfecto',
    'futuro': 'futuro',
    'future': 'futuro',
    'condicional': 'condicional',
    'conditional': 'condicional',
    'subjuntivo presente': 'subjuntivo',
    'present subjunctive': 'subjuntivo',
    'subjuntivo imperfecto': 'subjuntivo_imp',
    'past subjunctive': 'subjuntivo_imp',
}

PERSON_MAP = {
    'yo': ['yo', 'nosotros'],
    'tú': ['tú', 'vosotros'],
    'él/ella/Ud.': ['él/ella/Ud.', 'ellos/Uds.']
}

def parse_verb_file(filepath):
    """Parse a single verb .md file for conjugation data."""
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    # Get verb name from title: "# Ser — to be (essential, permanent)"
    verb_name = None
    verb_english = None
    for line in lines:
        m = re.match(r'^#\s+(\S+)\s+—\s+(.+)$', line)
        if m:
            verb_name = m.group(1).lower()
            verb_english = m.group(2).strip()
            break

    if not verb_name:
        return None, []

    # Skip pattern overview files (Regular -AR, Stem-Changing, etc.)
    if verb_name in ('regular', 'stem-changing', 'spelling-change', 'reflexive'):
        return None, []

    conjugations = {}
    current_tense = None

    for line in lines:
        # Check for tense header
        tm = TENSE_HEADER.match(line)
        if tm:
            tense_raw = tm.group(1).strip().lower()
            # Also check the parenthetical
            if tm.group(2):
                tense_raw2 = tm.group(2).strip().lower()
                mapped = TENSE_MAP.get(tense_raw2) or TENSE_MAP.get(tense_raw)
            else:
                mapped = TENSE_MAP.get(tense_raw)
            if mapped:
                current_tense = mapped
            continue

        # Check for conjugation table row
        if current_tense:
            cm = CONJ_TABLE_ROW.match(line)
            if cm:
                person_key = cm.group(1).strip()
                singular = cm.group(2).strip()
                plural = cm.group(3).strip()

                if current_tense not in conjugations:
                    conjugations[current_tense] = {}

                persons = PERSON_MAP.get(person_key, [person_key, person_key])
                # Clean up: strip pronoun prefixes from conjugated forms
                # Handles: "nosotros/as somos", "ellos/ellas/Uds. son", etc.
                PRONOUN_PREFIX = re.compile(
                    r'^(?:nosotros|vosotros|ellos|ellas|Uds\.|Ud\.)(?:/(?:as|os|ellas|Uds\.))*\s+'
                )
                sing_form = PRONOUN_PREFIX.sub('', singular).strip()
                plur_form = PRONOUN_PREFIX.sub('', plural).strip()

                # Strip markdown bold
                sing_form = sing_form.replace('**', '')
                plur_form = plur_form.replace('**', '')
                conjugations[current_tense][persons[0]] = sing_form
                conjugations[current_tense][persons[1]] = plur_form

    # Generate conjugation cards
    cards = []
    persons_order = ['yo', 'tú', 'él/ella/Ud.', 'nosotros', 'vosotros', 'ellos/Uds.']
    tenses_order = ['presente', 'pretérito', 'imperfecto', 'futuro', 'condicional', 'subjuntivo']

    for tense in tenses_order:
        if tense not in conjugations:
            continue
        for person in persons_order:
            form = conjugations[tense].get(person)
            if form and form not in ('', '—', '---'):
                cards.append({
                    'verb': verb_name,
                    'verbEn': verb_english,
                    'tense': tense,
                    'person': person,
                    'form': form,
                    'id': f"{verb_name}-{tense}-{person}"
                })

    return verb_name, cards

def export_conjugations():
    """Parse all individual verb files in Verbos/ for conjugation cards."""
    all_cards = []
    if not VERBOS_PATH.exists():
        print(f"  WARNING: {VERBOS_PATH} not found, skipping conjugations")
        return all_cards

    # Only parse individual verb files, not pattern overviews
    skip_files = {
        'regular -ar verbs.md', 'regular -er verbs.md', 'regular -ir verbs.md',
        'stem-changing verbs.md', 'spelling-change verbs.md', 'reflexive verbs.md'
    }

    for md_file in sorted(VERBOS_PATH.glob("*.md")):
        if md_file.name.lower() in skip_files:
            continue
        verb_name, cards = parse_verb_file(md_file)
        if cards:
            all_cards.extend(cards)

    print(f"  Conjugations: {len(all_cards)} cards from {len(set(c['verb'] for c in all_cards))} verbs")
    return all_cards

# ============================================================
# 3 & 4. MEDICAL VOCABULARY & PHRASES
# ============================================================
MED_PHRASE = re.compile(
    r'^-\s+\*\*(.+?)\*\*\s*—\s*(.+)$'
)

def harvest_medical_content():
    """Extract medical vocab and phrases from Verbos/ Medical Context sections."""
    med_vocab = []
    med_phrases = []
    seen_spanish = set()

    if not VERBOS_PATH.exists():
        return med_vocab, med_phrases

    for md_file in sorted(VERBOS_PATH.glob("*.md")):
        text = md_file.read_text(encoding='utf-8')

        # Find Medical Context section
        in_medical = False
        current_category = 'General'

        for line in text.split('\n'):
            if line.strip() == '## Medical Context':
                in_medical = True
                continue
            if in_medical and line.startswith('## ') and 'Medical' not in line:
                break  # Exited Medical Context section
            if in_medical and line.startswith('### '):
                current_category = line.replace('###', '').strip()
                continue

            if in_medical:
                m = MED_PHRASE.match(line)
                if m:
                    spanish = m.group(1).strip()
                    english = m.group(2).strip()

                    # Skip duplicates
                    sp_clean = spanish.lower().replace('¿', '').replace('?', '').strip()
                    if sp_clean in seen_spanish:
                        continue
                    seen_spanish.add(sp_clean)

                    # Everything from Medical Context goes to phrases
                    # (dedicated medical vocab files will go to med_vocab later)
                    med_phrases.append({
                        'es': spanish,
                        'en': english,
                        'category': current_category,
                        'source': md_file.stem
                    })

    # Also check Español Médico/ folder for dedicated files
    if MEDICO_PATH.exists():
        for md_file in sorted(MEDICO_PATH.glob("*.md")):
            text = md_file.read_text(encoding='utf-8')
            category = md_file.stem  # filename as category

            for line in text.split('\n'):
                m = MED_PHRASE.match(line)
                if m:
                    spanish = m.group(1).strip()
                    english = m.group(2).strip()
                    sp_clean = spanish.lower().replace('¿', '').replace('?', '').strip()
                    if sp_clean in seen_spanish:
                        continue
                    seen_spanish.add(sp_clean)

                    word_count = len(spanish.split())
                    target = med_vocab if word_count <= 2 else med_phrases
                    target.append({
                        'es': spanish,
                        'en': english,
                        'category': category,
                        'source': md_file.stem
                    })

    print(f"  Medical Vocab: {len(med_vocab)} terms")
    print(f"  Medical Phrases: {len(med_phrases)} phrases")
    return med_vocab, med_phrases

# ============================================================
# MAIN
# ============================================================
def main():
    print("SpanishKB Study — Data Export")
    print("=" * 40)

    print("\nExporting...")
    words = export_vocabulary()
    conjugations = export_conjugations()
    med_vocab, med_phrases = harvest_medical_content()

    data = {
        'meta': {
            'exportDate': datetime.now().isoformat(),
            'vaultPath': str(VAULT_PATH),
            'totalWords': len(words),
            'totalConjugations': len(conjugations),
            'totalMedVocab': len(med_vocab),
            'totalMedPhrases': len(med_phrases)
        },
        'words': words,
        'conjugations': conjugations,
        'medicalVocab': med_vocab,
        'medicalPhrases': med_phrases
    }

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\nOutput: {OUTPUT_PATH}")
    print(f"Size: {size_kb:.0f} KB")
    print(f"\nSummary:")
    print(f"  Words:        {len(words):,}")
    print(f"  Conjugations: {len(conjugations):,}")
    print(f"  Med Vocab:    {len(med_vocab):,}")
    print(f"  Med Phrases:  {len(med_phrases):,}")
    print(f"\nDone!")

if __name__ == '__main__':
    main()
