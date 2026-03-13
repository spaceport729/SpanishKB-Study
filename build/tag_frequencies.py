#!/usr/bin/env python3
"""
One-time script to add frequency tags {1}-{4} to all medical vocab/phrase files
and add new content from Stacey's docx + book photo sources.

Frequency Tiers (for ED nursing):
  {1} = Every patient encounter (vitals, pain, basic commands, allergies)
  {2} = Most shifts (common conditions, IV/blood draw, discharge, triage)
  {3} = Regular use (detailed anatomy, less common conditions, medical tests)
  {4} = Specialized/reference (rare conditions, admin terms, detailed anatomy)
"""

import re
from pathlib import Path

MEDICO = Path(r"C:\Users\stace\spaceport\SpanishKB\Español Médico")

# Default tier by file
FILE_TIERS = {
    'Clinical - Vitals and Signs': 1,
    'Clinical - Nursing Commands': 1,
    'Anatomy - Body': 2,
    'Anatomy - Head and Face': 2,
    'Anatomy - Heart': 2,
    'Anatomy - Respiratory': 2,
    'Anatomy - Digestive': 2,
    'Anatomy - Internal Organs': 2,
    'Anatomy - Skeleton': 3,
    'Anatomy - Blood': 3,
    'Anatomy - Circulation': 3,
    'Anatomy - Nervous System': 3,
    'Anatomy - Muscles': 3,
    'Anatomy - Joints': 3,
    'Anatomy - Urinary': 3,
    'Anatomy - Reproductive': 3,
    'Clinical - Measurements': 3,
    'Clinical - Hospital Locations': 2,
    'Phrases - Consent and Registration': 3,
    'Anatomy - Cells': 4,
    'Anatomy - Dental': 4,
    'Anatomy - Endocrine System': 4,
    'Anatomy - Eye and Ear': 3,
    'Anatomy - Hospital': 3,
    'Anatomy - Integumentary System': 4,
    'Anatomy - Lymphatic System': 4,
    'Anatomy - People': 2,
    'Expresiones - Conversational': 1,
    'Expresiones - Fillers and Connectors': 2,
    'Expresiones - Idioms': 3,
    'Expresiones - Time and Frequency': 2,
}

# Override specific items to different tiers (Spanish text → tier)
# These override the file default
TIER_OVERRIDES = {
    # Tier 1 overrides (critical every-patient terms)
    'el dolor': 1, 'la fiebre': 1, 'la presión arterial': 1,
    'la temperatura': 1, 'la frecuencia cardíaca / el pulso': 1,
    'el peso': 1, 'la saturación de oxígeno': 1,
    'el nivel de dolor': 1, 'el corazón': 1, 'los pulmones': 1,
    'el pecho': 1, 'la cabeza': 1, 'el estómago': 1, 'la espalda': 1,
    'el brazo': 1, 'la pierna': 1, 'la mano': 1, 'el pie': 1,
    'el cuello': 1, 'el abdomen': 1,
    'la sala de emergencia': 1, 'la sala de espera': 1,
    'el doctor / la doctora': 1, 'el/la enfermero/a': 1,
    'el/la paciente': 1, 'el/la paramédico/a': 1,
    # Tier 1 symptoms everyone asks about
    'la disnea': 1, 'el edema': 1,
    'el estómago revuelto': 1, 'la tos seca': 1,
    'la tos con flemas': 1,
    # Tier 1 equipment
    'el estetoscopio': 1, 'el tensiómetro / el esfigmomanómetro': 1,
    'el termómetro': 1, 'el oxímetro de pulso': 1,
    'la báscula': 1, 'la camilla': 1, 'la silla de ruedas': 1,
    'el monitor cardíaco': 1, 'el desfibrilador': 1,
    # Tier 2 overrides
    'la ictericia': 2, 'las sibilancias': 2, 'los estertores': 2,
    'la taquicardia': 2, 'la bradicardia': 2,
    'la cianosis': 2, 'la palidez': 2, 'la diaforesis': 2,
    'el laboratorio': 2, 'radiología': 2,
    'la sala de cuidados intensivos': 2, 'la sala de operaciones': 2,
    'la sala de partos': 2,
    'la entrada': 2, 'la salida': 2, 'el ascensor': 2,
    # Tier 2 people
    'el/la cirujano/a': 2, 'el/la técnico/a': 2,
    'el/la farmacéutico/a': 2, 'el/la intérprete': 2,
    'el/la trabajador/a social': 2,
    # Tier 4 overrides (specialized)
    'la rigidez de nuca': 4, 'el estridor': 3,
    'la apnea': 3, 'la taquipnea': 2,
    'la distensión abdominal': 3,
    'las pupilas dilatadas': 2, 'las pupilas contraídas': 2,
    'el reflejo pupilar': 3,
}

# Section-level tier overrides (section header text → tier)
SECTION_TIERS = {
    # Vitals and Signs
    'Vital Signs': 1,
    'Clinical Signs': 2,
    'Symptoms': 1,
    'Clinical Adjectives': 3,
    'Pain Assessment': 1,
    'Equipment': 2,
    # Nursing Commands
    'Triage and Intake': 1,
    'Assessment Questions': 1,
    'Physical Exam': 1,
    'IV and Blood Draw': 2,
    'Medication Administration': 2,
    'Patient Positioning': 2,
    'Discharge Instructions': 2,
}

LINE_RE = re.compile(r'^(-\s+\*\*(.+?)\*\*\s*—\s*.+?)(?:\s*\{\d\})?\s*$')

def tag_file(filepath, default_tier):
    """Add frequency tags to all items in a file."""
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')
    new_lines = []
    current_section_tier = default_tier

    for line in lines:
        # Track section headers for section-level overrides
        section_match = re.match(r'^##\s+(.+)', line)
        if section_match:
            section_name = section_match.group(1).strip()
            current_section_tier = SECTION_TIERS.get(section_name, default_tier)
            new_lines.append(line)
            continue

        m = LINE_RE.match(line)
        if m:
            content = m.group(1)  # Line without existing tag
            spanish = m.group(2).strip()

            # Determine tier: item override > section override > file default
            tier = TIER_OVERRIDES.get(spanish, current_section_tier)

            new_lines.append(f'{content} {{{tier}}}')
        else:
            new_lines.append(line)

    filepath.write_text('\n'.join(new_lines), encoding='utf-8')
    return len([l for l in new_lines if '{' in l and LINE_RE.match(l.replace('{', '').replace('}', '') + ' {3}')])


def add_new_content():
    """Add new medical content from Stacey's docx and book sources."""

    # ================================================================
    # NEW: Medical conditions vocab file
    # ================================================================
    conditions_file = MEDICO / 'Clinical - Conditions.md'
    conditions_content = """---
tags: [español-médico, clinical]
category: Conditions
---
# Condiciones y Enfermedades — Conditions and Diseases

## Common ED Conditions
- **la diabetes** — diabetes {2}
- **el asma** — asthma {2}
- **la bronquitis** — bronchitis {2}
- **la neumonía** — pneumonia {2}
- **la anemia** — anemia {2}
- **la hipertensión / la presión arterial alta** — hypertension / high blood pressure {1}
- **la hipotensión / la presión arterial baja** — hypotension / low blood pressure {2}
- **la hipoglucemia (se le baja el azúcar)** — hypoglycemia (low blood sugar) {2}
- **la hiperglucemia (se le sube el azúcar)** — hyperglycemia (high blood sugar) {2}
- **la infección** — infection {1}
- **las infecciones urinarias** — urinary tract infections {2}
- **la embolia / el derrame cerebral** — stroke {2}
- **las convulsiones / los ataques** — seizures {2}
- **la insuficiencia cardíaca (congestiva)** — congestive heart failure {2}
- **el infarto / el ataque al corazón** — heart attack {1}
- **la enfermedad pulmonar obstructiva crónica (EPOC)** — COPD {2}
- **la sepsis / la septicemia** — sepsis {2}
- **el tromboembolismo pulmonar** — pulmonary embolism {2}
- **el neumotórax** — pneumothorax {3}
- **la apendicitis** — appendicitis {2}
- **los cálculos en los riñones / piedra en el riñón** — kidney stones {2}
- **los cálculos biliares / piedras en la vesícula** — gallstones {2}
- **la pancreatitis** — pancreatitis {3}
- **la úlcera** — ulcer {3}
- **la indigestión** — indigestion {3}

## Infectious Diseases
- **la hepatitis A, B, C** — hepatitis A, B, C {2}
- **la tuberculosis** — tuberculosis {2}
- **la influenza / la gripe** — influenza / flu {2}
- **el VIH (virus de inmunodeficiencia humana)** — HIV {3}
- **el SIDA (síndrome de inmunodeficiencia adquirida)** — AIDS {3}
- **la sífilis** — syphilis {3}
- **la gonorrea** — gonorrhea {3}
- **la clamidia / clamidiasis** — chlamydia {3}
- **las enfermedades venéreas / enfermedades de transmisión sexual** — STDs / STIs {2}
- **las verrugas genitales** — genital warts {4}
- **las ladillas púbicas** — pubic lice {4}
- **la infección por hongos / candidiasis** — yeast infection / candidiasis {3}
- **el herpes** — herpes {3}
- **el herpes zóster / la culebrilla** — shingles {3}

## Childhood / Vaccine-Preventable
- **el sarampión / la rubéola** — measles {3}
- **las paperas** — mumps {4}
- **la amigdalitis** — tonsillitis {3}
- **la difteria** — diphtheria {4}
- **la tosferina / tos ferina** — whooping cough {4}
- **la fiebre tifoidea** — typhoid fever {4}
- **la poliomielitis** — polio {4}
- **la viruela** — smallpox {4}
- **la varicela** — chickenpox {3}

## Other Conditions
- **la fiebre reumática** — rheumatic fever {4}
- **la fiebre escarlatina** — scarlet fever {4}
- **la malaria / el paludismo** — malaria {4}
- **la disentería** — dysentery {4}
- **los parásitos** — parasites {3}
- **las lombrices intestinales** — intestinal worms {4}
- **la escabiosis / la sarna** — scabies {3}
- **las alergias** — allergies {1}
- **la rinitis alérgica** — allergic rhinitis / hay fever {3}
- **la adicción** — addiction {2}
- **la anorexia** — anorexia {3}
- **la ansiedad** — anxiety {2}
- **la depresión** — depression {2}
- **las hemorroides** — hemorrhoids {3}
- **la hernia** — hernia {3}
- **la hernia discal** — slipped disc {3}
- **la hiperventilación** — hyperventilation {2}
- **el insomnio** — insomnia {3}
- **la menopausia** — menopause {4}
- **el reumatismo** — rheumatism {4}
- **el sobrepeso** — overweight {3}
- **la epilepsia** — epilepsy {3}
- **la leucemia** — leukemia {4}
- **el cáncer** — cancer {3}
- **los tumores** — tumors {3}
- **las cataratas** — cataracts {4}
- **el glaucoma** — glaucoma {4}
- **el colesterol alto** — high cholesterol {3}
- **la enfermedad del corazón** — heart disease {2}
- **la enfermedad de Lyme** — Lyme disease {4}
- **el bocio** — goiter {4}
- **la parálisis cerebral** — cerebral palsy {4}
- **las várices / venas varicosas** — varicose veins {4}
- **el vértigo** — vertigo {2}
- **la conjuntivitis** — pink eye / conjunctivitis {3}
- **el cólico** — colic {3}

## Symptoms and Complaints
- **débil** — weak {1}
- **dolorido** — sore {2}
- **ensangrentado** — bloody {2}
- **el estornudo** — sneeze {3}
- **la fatiga** — fatigue {2}
- **hinchado** — swollen {1}
- **el moretón** — bruise {2}
- **el moqueo nasal** — runny nose {2}
- **la náusea** — nausea {1}
- **la pérdida de sangre** — bleeding / blood loss {1}
- **la erupción** — rash {2}
- **los espasmos** — spasms {3}
- **el estremecimiento** — shivering / trembling {3}
- **los ronquidos** — snoring {4}
- **el sangrado nasal** — nosebleed {2}
- **la sordera** — deafness {4}
- **el tartamudeo** — stuttering {4}

## Common Complaints (Patient Phrases)
- **Me mareo** — I feel dizzy {1}
- **Estoy con dolor** — I am in pain {1}
- **Estoy enfermo/enferma** — I'm sick {1}
- **Tengo diarrea** — I have diarrhea {1}
- **Tengo dolor de muelas** — I have a toothache {2}
- **Tengo frío** — I feel cold {2}
- **Tengo migraña** — I have a migraine {2}
- **Tengo vértigos** — I feel vertigo {2}
- **Me duele la cabeza** — My head hurts {1}
- **Me duele el pecho** — My chest hurts {1}
- **Me duele el estómago** — My stomach hurts {1}
- **No puedo respirar** — I can't breathe {1}
- **Me siento débil** — I feel weak {1}
- **Tengo náuseas** — I feel nauseous {1}
- **Estoy sangrando** — I am bleeding {1}
- **Me caí** — I fell {1}
- **Tengo dolor de garganta** — I have a sore throat {2}
- **Tengo dolor punzante** — I have a throbbing/stabbing pain {2}
"""
    conditions_file.write_text(conditions_content.strip(), encoding='utf-8')
    print(f"  Created: {conditions_file.name}")

    # ================================================================
    # NEW: Medical tests and procedures vocab
    # ================================================================
    tests_file = MEDICO / 'Clinical - Tests and Procedures.md'
    tests_content = """---
tags: [español-médico, clinical]
category: Tests and Procedures
---
# Exámenes y Procedimientos — Tests and Procedures

## Common ED Tests
- **la radiografía / los rayos X** — X-ray {1}
- **el análisis de sangre** — blood test {1}
- **el análisis de orina** — urine test / urinalysis {1}
- **la tomografía computarizada (CT/CAT scan)** — CT scan {2}
- **la resonancia magnética (RM)** — MRI {2}
- **la ecografía / el ultrasonido** — ultrasound {2}
- **el electrocardiograma (ECG/EKG)** — electrocardiogram {1}
- **la prueba de embarazo** — pregnancy test {2}
- **el hemograma completo** — complete blood count (CBC) {2}
- **el panel metabólico** — metabolic panel {2}
- **los gases arteriales** — arterial blood gas (ABG) {2}
- **el cultivo** — culture {2}
- **la prueba rápida de estreptococo** — rapid strep test {3}
- **la prueba de influenza** — flu test {2}
- **la troponina** — troponin {2}
- **el dímero-D** — D-dimer {3}
- **el lactato** — lactate {2}
- **el tipo de sangre** — blood type {2}

## Specialized Tests
- **la endoscopia** — endoscopy {3}
- **la colonoscopía** — colonoscopy {3}
- **la biopsia** — biopsy {3}
- **la mamografía** — mammogram {4}
- **la electroencefalografía (EEG)** — electroencephalography (EEG) {4}
- **la electrocardiografía** — electrocardiography (ECG) {3}
- **la coronariografía** — coronary angiogram {4}
- **el análisis de heces** — stool test / fecalysis {3}
- **la prueba de esfuerzo** — stress test {4}
- **la punción lumbar** — lumbar puncture / spinal tap {3}

## Spanish Medical Abbreviations
- **ECV (enfermedad cerebrovascular)** — cerebrovascular disease / stroke {3}
- **EPOC (enfermedad pulmonar obstructiva crónica)** — COPD {2}
- **SNC (sistema nervioso central)** — central nervous system (CNS) {3}
- **SSN (solución salina normal)** — normal saline (NS) {2}
- **ICC (insuficiencia cardíaca congestiva)** — congestive heart failure (CHF) {2}
- **VIH (virus de inmunodeficiencia humana)** — HIV {3}
- **SIDA (síndrome de inmunodeficiencia adquirida)** — AIDS {3}
- **SDR (síndrome de distrés respiratorio)** — respiratory distress syndrome {3}
- **PAM (presión arterial media)** — mean arterial pressure (MAP) {2}
- **RAO (retención aguda de orina)** — acute urinary retention {3}
- **ERC (enfermedad renal crónica)** — chronic kidney disease (CKD) {3}
"""
    tests_file.write_text(tests_content.strip(), encoding='utf-8')
    print(f"  Created: {tests_file.name}")

    # ================================================================
    # NEW: Medication instruction phrases
    # ================================================================
    meds_file = MEDICO / 'Phrases - Medication Instructions.md'
    meds_content = """---
tags: [español-médico, clinical]
category: Medication Instructions
---
# Instrucciones de Medicamentos — Medication Instructions

## Prescriptions
- **Voy a explicar la receta** — I'm going to explain the prescription {2}
- **Aquí tiene la dosis** — Here you have the dosage {2}
- **Tiene que llevar la receta a la farmacia** — You need to take the prescription to the pharmacy {2}
- **¿Tiene alergias a algún fármaco?** — Are you allergic to any medication? {1}
- **¿Necesita algo fuerte para el dolor?** — Do you need something strong for the pain? {1}

## Dosing Instructions
- **Tome esta medicina...** — Take this medicine... {1}
- **...veces al día** — ...times a day {1}
- **...cada ___ horas** — ...every ___ hours {1}
- **Tomar una vez al día con la comida** — Take once a day with food {2}
- **disuelta en agua** — dissolved in water {3}
- **con cada comida** — with each meal {2}
- **antes de cada comida** — before each meal {2}
- **después de cada comida** — after each meal {2}
- **antes de acostarse** — before going to bed {2}
- **Disuelva una tableta/pastilla debajo de la lengua** — Dissolve a tablet under your tongue {2}

## Warnings and Side Effects
- **Este medicamento puede causar sueño/somnolencia** — This medication may cause drowsiness {2}
- **Agite bien antes de usar** — Shake well before using {3}
- **Manténgala refrigerada** — Keep it refrigerated {3}
- **No tome con alcohol** — Do not take with alcohol {2}
- **No maneje después de tomar este medicamento** — Don't drive after taking this medication {2}
- **Puede causar mareos** — May cause dizziness {2}
- **Puede causar náuseas** — May cause nausea {2}
- **Llame si tiene una reacción alérgica** — Call if you have an allergic reaction {2}

## Discharge Medication
- **El alta hospitalaria** — Hospital discharge {2}
- **Aquí tiene sus recetas** — Here are your prescriptions {2}
- **Siga tomando su medicamento habitual** — Continue taking your regular medication {2}
- **No deje de tomar su medicamento sin consultar a su médico** — Don't stop taking your medication without consulting your doctor {2}
"""
    meds_file.write_text(meds_content.strip(), encoding='utf-8')
    print(f"  Created: {meds_file.name}")

    # ================================================================
    # NEW: Medical history questions
    # ================================================================
    history_file = MEDICO / 'Phrases - Medical History.md'
    history_content = """---
tags: [español-médico, clinical]
category: Medical History
---
# Historia Clínica — Medical History Questions

## Current Visit
- **¿Qué le trae hoy?** — What brings you in today? {1}
- **¿Cuándo empezó?** — When did it start? {1}
- **¿Cuánto tiempo tiene con este problema?** — How long have you had this problem? {1}
- **¿Ha empeorado o mejorado?** — Has it gotten worse or better? {1}
- **¿Tiene algún otro síntoma?** — Do you have any other symptoms? {1}
- **¿Qué estaba haciendo cuando empezó?** — What were you doing when it started? {1}

## Past Medical History
- **¿Tiene alguna enfermedad crónica?** — Do you have any chronic illness? {1}
- **¿Está tomando alguna medicina?** — Are you taking any medication? {1}
- **¿Tiene reacción alérgica o problemas con alguna medicina?** — Do you have an allergic reaction or problems with any medication? {1}
- **¿Ha tenido cirugías?** — Have you had surgeries? {2}
- **¿Ha sido hospitalizado/a antes?** — Have you been hospitalized before? {2}
- **¿Cuándo fue su última visita al médico?** — When was your last doctor visit? {2}

## Social History
- **¿Fuma?** — Do you smoke? {1}
- **¿Cuántos cigarrillos por día?** — How many cigarettes per day? {2}
- **¿Toma bebidas alcohólicas?** — Do you drink alcohol? {1}
- **¿Cuántas bebidas por semana?** — How many drinks per week? {2}
- **¿Usa drogas?** — Do you use drugs? {1}
- **¿Qué tipo de drogas?** — What type of drugs? {2}

## Family History
- **¿Hay enfermedades en su familia?** — Are there diseases in your family? {2}
- **¿Alguien en su familia tiene diabetes?** — Does anyone in your family have diabetes? {2}
- **¿Alguien en su familia tiene problemas del corazón?** — Does anyone in your family have heart problems? {2}
- **¿Alguien en su familia ha tenido cáncer?** — Has anyone in your family had cancer? {3}
- **¿Alguien en su familia ha tenido derrame cerebral?** — Has anyone in your family had a stroke? {3}

## OB/GYN History
- **¿Cuándo fue su última menstruación?** — When was your last period? {2}
- **¿Tiene reglas dolorosas?** — Do you have painful periods? {3}
- **¿Está embarazada o podría estar embarazada?** — Are you pregnant or could you be pregnant? {1}
- **¿Cuántos embarazos ha tenido?** — How many pregnancies have you had? {2}
- **¿Tuvo problemas durante su embarazo?** — Did you have problems during your pregnancy? {3}
- **¿Fueron los partos normales o cesáreas?** — Were the deliveries vaginal or C-sections? {3}
- **¿Ha tenido diabetes durante un embarazo?** — Have you had diabetes during a pregnancy? {3}
- **¿Usa algún método anticonceptivo?** — Do you use any birth control? {3}

## Contraception Vocabulary
- **la píldora / las pastillas anticonceptivas** — birth control pills {3}
- **el diafragma** — diaphragm {4}
- **los condones / los preservativos** — condoms {3}
- **el parche** — the patch {4}
- **las inyecciones / Depo-Provera** — injections / Depo-Provera {4}
- **el dispositivo intrauterino (DIU)** — IUD {3}
- **la ligadura de trompas** — tubal ligation {4}
- **la vasectomía** — vasectomy {4}
"""
    history_file.write_text(history_content.strip(), encoding='utf-8')
    print(f"  Created: {history_file.name}")

    # ================================================================
    # NEW: Physical exam commands (additions from book)
    # ================================================================
    # These will be added to the existing Nursing Commands file
    nursing_file = MEDICO / 'Clinical - Nursing Commands.md'
    text = nursing_file.read_text(encoding='utf-8')

    # Add new commands that aren't already there
    new_exam_commands = """
## Additional Exam Commands
- **Trague saliva** — Swallow {2}
- **Acuéstese** — Lie down {1}
- **Mire este punto** — Look at this point {2}
- **Mire esta luz** — Look at this light {2}
- **Otra vez** — Again {1}
- **Palpe / sienta** — Touch / feel {2}
- **Baje el brazo** — Lower your arm {2}
- **Suba la pierna** — Raise your leg {2}
- **Extienda los brazos hacia el frente** — Extend your arms in front {2}
- **Apriete mis dedos** — Squeeze my fingers {2}
- **Palmas hacia arriba** — Palms up {2}
- **Suba los hombros** — Raise your shoulders {2}
- **Resista** — Resist {2}
- **De vuelta** — Turn around {2}
- **Cierre** — Close {2}
- **Abra** — Open {1}
- **Toque** — Touch {2}
- **Mire** — Look {2}
- **Puntillas** — Stand on tiptoe {3}
- **Muerda** — Bite {3}
- **Hale** — Pull {2}
- **Empuje** — Push {2}
- **Infle los cachetes** — Puff out your cheeks {3}
"""
    if '## Additional Exam Commands' not in text:
        text = text.rstrip() + '\n' + new_exam_commands
        nursing_file.write_text(text, encoding='utf-8')
        print(f"  Updated: {nursing_file.name} (added exam commands)")


def main():
    print("Tagging frequency tiers on medical files...")
    print("=" * 50)

    # Tag existing files
    total_tagged = 0
    for md_file in sorted(MEDICO.glob("*.md")):
        stem = md_file.stem
        default_tier = FILE_TIERS.get(stem, 3)
        tag_file(md_file, default_tier)
        print(f"  Tagged: {md_file.name} (default T{default_tier})")
        total_tagged += 1

    print(f"\n  Tagged {total_tagged} existing files")

    # Add new content
    print("\nAdding new content from sources...")
    add_new_content()

    # Tag the new files too
    print("\nTagging new files...")
    for new_file in ['Clinical - Conditions.md', 'Clinical - Tests and Procedures.md',
                     'Phrases - Medication Instructions.md', 'Phrases - Medical History.md']:
        fp = MEDICO / new_file
        if fp.exists():
            stem = fp.stem
            default_tier = FILE_TIERS.get(stem, 3)
            tag_file(fp, default_tier)

    print("\nDone! Run export_data.py to rebuild data.json")


if __name__ == '__main__':
    main()
