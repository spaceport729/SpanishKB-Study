#!/usr/bin/env python3
"""
SpanishKB Study PWA — Data Export Script
Parses SpanishKB vault and exports data.json for the study app.

Exports seven data types:
  1. words               — 5,000 frequency-ranked vocabulary from Vocabulario/*.md
  2. conjugationPatterns  — regular verb ending patterns (~141 cards)
  3. conjugationIrregulars — irregular verb forms only (~3,000 cards)
  4. medicalVocab        — medical vocabulary from Español Médico/ anatomy files
  5. medicalPhrases      — clinical phrases from Verbos/ + ClinicalKB
  6. expressions         — idioms, conversational phrases, fillers
  7. grammarNotes        — grammar reference content from Grammar Notes.md
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

def export_conjugation_patterns_and_irregulars(vocab_words=None):
    """
    Generate two sets of conjugation cards:
    1. Pattern cards — regular endings (~141 cards, teach the rules)
    2. Irregular cards — only forms that deviate from regular (~3,000 cards)
    """
    from conjugator import (
        generate_pattern_cards, conjugate_to_irregular_cards,
        get_verb_group, is_verb_irregular
    )

    # --- Pattern cards ---
    patterns = generate_pattern_cards()
    print(f"  Conjugation patterns: {len(patterns)} cards")

    # --- Irregular cards from vocabulary verbs ---
    irregulars = []
    if vocab_words:
        irr_verbs = 0
        for w in vocab_words:
            if w.get('type') not in ('v', 'v/aux'):
                continue
            infinitive = w['es'].split(',')[0].strip()
            if not get_verb_group(infinitive):
                continue
            cards = conjugate_to_irregular_cards(
                infinitive, w.get('en', ''), rank=w.get('rank', 9999)
            )
            if cards:
                irregulars.extend(cards)
                irr_verbs += 1

        irregulars.sort(key=lambda c: c.get('sortKey', 999999))
        print(f"  Irregular verbs: {irr_verbs} verbs, {len(irregulars)} cards")
        # Show top irregular verbs
        seen = []
        for c in irregulars:
            if c['verb'] not in seen:
                seen.append(c['verb'])
                if len(seen) >= 10:
                    break
        print(f"  Top 10 irregular: {', '.join(seen)}")

    return patterns, irregulars

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
            # Skip Expresiones files — they go to expressions export
            if md_file.stem.startswith('Expresiones'):
                continue
            text = md_file.read_text(encoding='utf-8')
            category = md_file.stem  # filename as category

            # Command/instruction files → phrases; everything else → vocab
            is_phrases = 'Commands' in md_file.stem or 'Instructions' in md_file.stem

            for line in text.split('\n'):
                m = MED_PHRASE.match(line)
                if m:
                    spanish = m.group(1).strip()
                    english = m.group(2).strip()
                    sp_clean = spanish.lower().replace('¿', '').replace('?', '').strip()
                    if sp_clean in seen_spanish:
                        continue
                    seen_spanish.add(sp_clean)

                    target = med_phrases if is_phrases else med_vocab
                    target.append({
                        'es': spanish,
                        'en': english,
                        'category': category,
                        'source': md_file.stem
                    })

    # Also check ClinicalKB for Spanish Clinical Questions
    CLINICAL_SPANISH = Path(r"C:\Users\stace\spaceport\ClinicalKB\Spanish Clinical Questions — ED Chief Complaints.md")
    if CLINICAL_SPANISH.exists():
        text = CLINICAL_SPANISH.read_text(encoding='utf-8')
        current_category = 'General'
        # Parse markdown tables: | English | Español |
        TABLE_ROW = re.compile(r'^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$')
        # Parse vocab tables: | spanish: english | ... |
        VOCAB_CELL = re.compile(r'([^|:]+):\s*([^|]+)')

        for line in text.split('\n'):
            # Track section headers
            hm = re.match(r'^##\s+(.+)', line)
            if hm:
                current_category = hm.group(1).strip()
                continue

            # Skip table headers and separator rows
            if '---' in line and '|' in line:
                continue
            if '| English' in line or '| Español' in line:
                continue

            # Parse vocab rows first (multi-cell format: | word: translation | word: translation |)
            if current_category == 'Vocabulary' and '|' in line and ':' in line:
                for cell_m in VOCAB_CELL.finditer(line):
                    spanish = cell_m.group(1).strip()
                    english = cell_m.group(2).strip()
                    if not spanish or not english:
                        continue
                    sp_clean = spanish.lower().replace('¿', '').replace('?', '').strip()
                    if sp_clean in seen_spanish:
                        continue
                    seen_spanish.add(sp_clean)
                    med_vocab.append({
                        'es': spanish,
                        'en': english,
                        'category': 'ED Vocabulary',
                        'source': 'Spanish Clinical Questions'
                    })
                continue

            # Parse two-column tables (English | Español)
            tm = TABLE_ROW.match(line)
            if tm:
                english = tm.group(1).strip()
                spanish = tm.group(2).strip()

                # Skip empty cells or header-like content
                if not english or not spanish:
                    continue
                if english.lower() in ('english', 'español', ''):
                    continue

                sp_clean = spanish.lower().replace('¿', '').replace('?', '').strip()
                if sp_clean in seen_spanish:
                    continue
                seen_spanish.add(sp_clean)

                med_phrases.append({
                    'es': spanish,
                    'en': english,
                    'category': current_category,
                    'source': 'Spanish Clinical Questions'
                })

        clinical_count = sum(1 for p in med_phrases if p['source'] == 'Spanish Clinical Questions')
        clinical_vocab = sum(1 for v in med_vocab if v['source'] == 'Spanish Clinical Questions')
        print(f"  Clinical Spanish: {clinical_count} phrases, {clinical_vocab} vocab terms")

    print(f"  Medical Vocab: {len(med_vocab)} terms")
    print(f"  Medical Phrases: {len(med_phrases)} phrases")
    return med_vocab, med_phrases

# ============================================================
# 5. EXPRESSIONS
# ============================================================
EXPR_PATTERN = re.compile(
    r'^-\s+\*\*(.+?)\*\*\s*—\s*(.+)$'
)

def export_expressions():
    """Export expressions from Expresiones-*.md files in Español Médico/."""
    expressions = []
    seen = set()

    if not MEDICO_PATH.exists():
        return expressions

    for md_file in sorted(MEDICO_PATH.glob("Expresiones*.md")):
        text = md_file.read_text(encoding='utf-8')

        # Get category from frontmatter or filename
        fm = parse_frontmatter(text)
        file_category = fm.get('category', md_file.stem.replace('Expresiones - ', ''))

        current_section = file_category

        for line in text.split('\n'):
            # Track subsection headers
            hm = re.match(r'^##\s+(.+)', line)
            if hm:
                current_section = hm.group(1).strip()
                continue

            m = EXPR_PATTERN.match(line)
            if m:
                spanish = m.group(1).strip()
                english = m.group(2).strip()

                sp_clean = spanish.lower().replace('¿', '').replace('?', '').replace('¡', '').replace('!', '').strip()
                if sp_clean in seen:
                    continue
                seen.add(sp_clean)

                expressions.append({
                    'es': spanish,
                    'en': english,
                    'category': current_section,
                    'source': md_file.stem
                })

    print(f"  Expressions: {len(expressions)} items")
    return expressions

# ============================================================
# 6. GRAMMAR NOTES
# ============================================================
def export_grammar_notes():
    """Export Grammar Notes.md as structured sections for the reference view."""
    grammar_file = VAULT_PATH / "Grammar Notes.md"
    if not grammar_file.exists():
        print("  Grammar Notes: not found")
        return []

    text = grammar_file.read_text(encoding='utf-8')
    sections = []
    current_section = None
    current_content = []

    for line in text.split('\n'):
        # Skip frontmatter
        if line.strip() == '---':
            continue
        if line.startswith('tags:') or line.startswith('# Grammar Notes'):
            continue

        # New section at ## level
        if line.startswith('## '):
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line.replace('## ', '').strip()
            current_content = []
            continue

        if current_section:
            current_content.append(line)

    # Don't forget the last section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })

    print(f"  Grammar Notes: {len(sections)} sections")
    return sections


# ============================================================
# MAIN
# ============================================================
def main():
    print("SpanishKB Study \u2014 Data Export")
    print("=" * 40)

    print("\nExporting...")
    words = export_vocabulary()
    patterns, irregulars = export_conjugation_patterns_and_irregulars(vocab_words=words)
    med_vocab, med_phrases = harvest_medical_content()
    expressions = export_expressions()
    grammar_notes = export_grammar_notes()

    data = {
        'meta': {
            'exportDate': datetime.now().isoformat(),
            'vaultPath': str(VAULT_PATH),
            'totalWords': len(words),
            'totalPatterns': len(patterns),
            'totalIrregulars': len(irregulars),
            'totalMedVocab': len(med_vocab),
            'totalMedPhrases': len(med_phrases),
            'totalExpressions': len(expressions),
            'totalGrammarSections': len(grammar_notes)
        },
        'words': words,
        'conjugationPatterns': patterns,
        'conjugationIrregulars': irregulars,
        'medicalVocab': med_vocab,
        'medicalPhrases': med_phrases,
        'expressions': expressions,
        'grammarNotes': grammar_notes
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
    print(f"  Patterns:     {len(patterns):,}")
    print(f"  Irregulars:   {len(irregulars):,}")
    print(f"  Med Vocab:    {len(med_vocab):,}")
    print(f"  Med Phrases:  {len(med_phrases):,}")
    print(f"  Expressions:  {len(expressions):,}")
    print(f"  Grammar:      {len(grammar_notes)} sections")
    print(f"\nDone!")

if __name__ == '__main__':
    main()
