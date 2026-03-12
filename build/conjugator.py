"""
Spanish Verb Conjugation Engine
Generates conjugations for regular, stem-changing, spelling-change, and irregular verbs.
Covers 6 tenses × 6 persons = up to 36 forms per verb.
"""

# ============================================================
# REGULAR ENDINGS
# ============================================================
# Format: {tense: {ending_group: [yo, tú, él, nosotros, vosotros, ellos]}}
REGULAR = {
    'presente': {
        'ar': ['o', 'as', 'a', 'amos', 'áis', 'an'],
        'er': ['o', 'es', 'e', 'emos', 'éis', 'en'],
        'ir': ['o', 'es', 'e', 'imos', 'ís', 'en'],
    },
    'pretérito': {
        'ar': ['é', 'aste', 'ó', 'amos', 'asteis', 'aron'],
        'er': ['í', 'iste', 'ió', 'imos', 'isteis', 'ieron'],
        'ir': ['í', 'iste', 'ió', 'imos', 'isteis', 'ieron'],
    },
    'imperfecto': {
        'ar': ['aba', 'abas', 'aba', 'ábamos', 'abais', 'aban'],
        'er': ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],
        'ir': ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],
    },
    'futuro': {
        'ar': ['é', 'ás', 'á', 'emos', 'éis', 'án'],
        'er': ['é', 'ás', 'á', 'emos', 'éis', 'án'],
        'ir': ['é', 'ás', 'á', 'emos', 'éis', 'án'],
    },
    'condicional': {
        'ar': ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],
        'er': ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],
        'ir': ['ía', 'ías', 'ía', 'íamos', 'íais', 'ían'],
    },
    'subjuntivo': {
        'ar': ['e', 'es', 'e', 'emos', 'éis', 'en'],
        'er': ['a', 'as', 'a', 'amos', 'áis', 'an'],
        'ir': ['a', 'as', 'a', 'amos', 'áis', 'an'],
    },
}

PERSONS = ['yo', 'tú', 'él/ella/Ud.', 'nosotros', 'vosotros', 'ellos/Uds.']

# ============================================================
# STEM-CHANGING VERBS
# ============================================================
# Stem changes apply in presente (all except nosotros/vosotros) and subjuntivo
# Some also change in pretérito (e→i, o→u) for -ir verbs in él/ellos
# Format: {infinitive: (change_type, group)}
# change_type: 'e>ie', 'o>ue', 'e>i', 'u>ue', 'i>ie'
STEM_CHANGERS = {
    # e → ie
    'pensar': 'e>ie', 'cerrar': 'e>ie', 'comenzar': 'e>ie', 'despertar': 'e>ie',
    'empezar': 'e>ie', 'entender': 'e>ie', 'perder': 'e>ie', 'querer': 'e>ie',
    'defender': 'e>ie', 'encender': 'e>ie', 'sentir': 'e>ie', 'preferir': 'e>ie',
    'mentir': 'e>ie', 'divertir': 'e>ie', 'convertir': 'e>ie', 'hervir': 'e>ie',
    'referir': 'e>ie', 'sugerir': 'e>ie', 'advertir': 'e>ie', 'consentir': 'e>ie',
    'negar': 'e>ie', 'regar': 'e>ie', 'confesar': 'e>ie', 'calentar': 'e>ie',
    'sentar': 'e>ie', 'apretar': 'e>ie', 'atravesar': 'e>ie', 'gobernar': 'e>ie',
    'temblar': 'e>ie', 'sembrar': 'e>ie', 'recomendar': 'e>ie',
    'ascender': 'e>ie', 'descender': 'e>ie', 'atender': 'e>ie', 'tender': 'e>ie',
    'extender': 'e>ie',
    # o → ue
    'poder': 'o>ue', 'volver': 'o>ue', 'dormir': 'o>ue', 'morir': 'o>ue',
    'contar': 'o>ue', 'encontrar': 'o>ue', 'recordar': 'o>ue', 'mostrar': 'o>ue',
    'costar': 'o>ue', 'mover': 'o>ue', 'soler': 'o>ue', 'devolver': 'o>ue',
    'resolver': 'o>ue', 'probar': 'o>ue', 'comprobar': 'o>ue', 'aprobar': 'o>ue',
    'rogar': 'o>ue', 'colgar': 'o>ue', 'sonar': 'o>ue', 'soñar': 'o>ue',
    'volar': 'o>ue', 'renovar': 'o>ue', 'almorzar': 'o>ue', 'forzar': 'o>ue',
    'esforzar': 'o>ue', 'torcer': 'o>ue', 'morder': 'o>ue', 'llover': 'o>ue',
    'doler': 'o>ue', 'tronar': 'o>ue', 'acordar': 'o>ue', 'soltar': 'o>ue',
    'consolar': 'o>ue',
    # e → i (only -ir verbs)
    'pedir': 'e>i', 'repetir': 'e>i', 'seguir': 'e>i', 'servir': 'e>i',
    'vestir': 'e>i', 'medir': 'e>i', 'elegir': 'e>i', 'corregir': 'e>i',
    'perseguir': 'e>i', 'conseguir': 'e>i', 'impedir': 'e>i', 'despedir': 'e>i',
    'competir': 'e>i', 'reír': 'e>i', 'sonreír': 'e>i', 'freír': 'e>i',
    'rendir': 'e>i', 'derretir': 'e>i', 'gemir': 'e>i',
    # u → ue
    'jugar': 'u>ue',
}

def apply_stem_change(stem, change_type):
    """Apply stem change to the LAST occurrence of the vowel in the stem."""
    if change_type == 'e>ie':
        idx = stem.rfind('e')
        if idx >= 0:
            return stem[:idx] + 'ie' + stem[idx+1:]
    elif change_type == 'o>ue':
        idx = stem.rfind('o')
        if idx >= 0:
            return stem[:idx] + 'ue' + stem[idx+1:]
    elif change_type == 'e>i':
        idx = stem.rfind('e')
        if idx >= 0:
            return stem[:idx] + 'i' + stem[idx+1:]
    elif change_type == 'u>ue':
        idx = stem.rfind('u')
        if idx >= 0:
            return stem[:idx] + 'ue' + stem[idx+1:]
    elif change_type == 'i>ie':
        idx = stem.rfind('i')
        if idx >= 0:
            return stem[:idx] + 'ie' + stem[idx+1:]
    return stem


# ============================================================
# SPELLING CHANGES
# ============================================================
def spelling_fix_pretérito_yo(stem, group):
    """Fix spelling changes in pretérito yo form for -ar verbs."""
    if group != 'ar':
        return stem
    # c → qu before é (buscar → busqué)
    if stem.endswith('c'):
        return stem[:-1] + 'qu'
    # g → gu before é (pagar → pagué)
    if stem.endswith('g'):
        return stem + 'u'
    # z → c before é (empezar → empecé)
    if stem.endswith('z'):
        return stem[:-1] + 'c'
    return stem

def spelling_fix_subjuntivo(stem, group):
    """Fix spelling changes in subjuntive for the whole paradigm."""
    if group == 'ar':
        # c → qu before e (buscar → busque)
        if stem.endswith('c'):
            return stem[:-1] + 'qu'
        # g → gu before e (pagar → pague)
        if stem.endswith('g'):
            return stem + 'u'
        # z → c before e (empezar → empiece — but stem change handles the ie)
        if stem.endswith('z'):
            return stem[:-1] + 'c'
    elif group in ('er', 'ir'):
        # g → j before a (coger → coja)
        if stem.endswith('g'):
            return stem[:-1] + 'j'
        # gu → g before a (seguir → siga — gu drops u)
        if stem.endswith('gu'):
            return stem[:-1]  # drop the u
        # c → z before a (convencer → convenza)
        if stem.endswith('c'):
            return stem[:-1] + 'z'
    return stem


# ============================================================
# IRREGULAR VERBS — full override forms
# ============================================================
# Only tenses that are irregular; regular tenses fall through.
# None means "skip this person" (shouldn't happen, but safety)
IRREGULARS = {
    'ser': {
        'presente': ['soy', 'eres', 'es', 'somos', 'sois', 'son'],
        'pretérito': ['fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron'],
        'imperfecto': ['era', 'eras', 'era', 'éramos', 'erais', 'eran'],
        'subjuntivo': ['sea', 'seas', 'sea', 'seamos', 'seáis', 'sean'],
    },
    'estar': {
        'presente': ['estoy', 'estás', 'está', 'estamos', 'estáis', 'están'],
        'pretérito': ['estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron'],
        'subjuntivo': ['esté', 'estés', 'esté', 'estemos', 'estéis', 'estén'],
    },
    'ir': {
        'presente': ['voy', 'vas', 'va', 'vamos', 'vais', 'van'],
        'pretérito': ['fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron'],
        'imperfecto': ['iba', 'ibas', 'iba', 'íbamos', 'ibais', 'iban'],
        'subjuntivo': ['vaya', 'vayas', 'vaya', 'vayamos', 'vayáis', 'vayan'],
    },
    'haber': {
        'presente': ['he', 'has', 'ha', 'hemos', 'habéis', 'han'],
        'pretérito': ['hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron'],
        'futuro': ['habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán'],
        'condicional': ['habría', 'habrías', 'habría', 'habríamos', 'habríais', 'habrían'],
        'subjuntivo': ['haya', 'hayas', 'haya', 'hayamos', 'hayáis', 'hayan'],
    },
    'tener': {
        'presente': ['tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen'],
        'pretérito': ['tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron'],
        'futuro': ['tendré', 'tendrás', 'tendrá', 'tendremos', 'tendréis', 'tendrán'],
        'condicional': ['tendría', 'tendrías', 'tendría', 'tendríamos', 'tendríais', 'tendrían'],
        'subjuntivo': ['tenga', 'tengas', 'tenga', 'tengamos', 'tengáis', 'tengan'],
    },
    'hacer': {
        'presente': ['hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen'],
        'pretérito': ['hice', 'hiciste', 'hizo', 'hicimos', 'hicisteis', 'hicieron'],
        'futuro': ['haré', 'harás', 'hará', 'haremos', 'haréis', 'harán'],
        'condicional': ['haría', 'harías', 'haría', 'haríamos', 'haríais', 'harían'],
        'subjuntivo': ['haga', 'hagas', 'haga', 'hagamos', 'hagáis', 'hagan'],
    },
    'decir': {
        'presente': ['digo', 'dices', 'dice', 'decimos', 'decís', 'dicen'],
        'pretérito': ['dije', 'dijiste', 'dijo', 'dijimos', 'dijisteis', 'dijeron'],
        'futuro': ['diré', 'dirás', 'dirá', 'diremos', 'diréis', 'dirán'],
        'condicional': ['diría', 'dirías', 'diría', 'diríamos', 'diríais', 'dirían'],
        'subjuntivo': ['diga', 'digas', 'diga', 'digamos', 'digáis', 'digan'],
    },
    'venir': {
        'presente': ['vengo', 'vienes', 'viene', 'venimos', 'venís', 'vienen'],
        'pretérito': ['vine', 'viniste', 'vino', 'vinimos', 'vinisteis', 'vinieron'],
        'futuro': ['vendré', 'vendrás', 'vendrá', 'vendremos', 'vendréis', 'vendrán'],
        'condicional': ['vendría', 'vendrías', 'vendría', 'vendríamos', 'vendríais', 'vendrían'],
        'subjuntivo': ['venga', 'vengas', 'venga', 'vengamos', 'vengáis', 'vengan'],
    },
    'poner': {
        'presente': ['pongo', 'pones', 'pone', 'ponemos', 'ponéis', 'ponen'],
        'pretérito': ['puse', 'pusiste', 'puso', 'pusimos', 'pusisteis', 'pusieron'],
        'futuro': ['pondré', 'pondrás', 'pondrá', 'pondremos', 'pondréis', 'pondrán'],
        'condicional': ['pondría', 'pondrías', 'pondría', 'pondríamos', 'pondríais', 'pondrían'],
        'subjuntivo': ['ponga', 'pongas', 'ponga', 'pongamos', 'pongáis', 'pongan'],
    },
    'salir': {
        'presente': ['salgo', 'sales', 'sale', 'salimos', 'salís', 'salen'],
        'futuro': ['saldré', 'saldrás', 'saldrá', 'saldremos', 'saldréis', 'saldrán'],
        'condicional': ['saldría', 'saldrías', 'saldría', 'saldríamos', 'saldríais', 'saldrían'],
        'subjuntivo': ['salga', 'salgas', 'salga', 'salgamos', 'salgáis', 'salgan'],
    },
    'saber': {
        'presente': ['sé', 'sabes', 'sabe', 'sabemos', 'sabéis', 'saben'],
        'pretérito': ['supe', 'supiste', 'supo', 'supimos', 'supisteis', 'supieron'],
        'futuro': ['sabré', 'sabrás', 'sabrá', 'sabremos', 'sabréis', 'sabrán'],
        'condicional': ['sabría', 'sabrías', 'sabría', 'sabríamos', 'sabríais', 'sabrían'],
        'subjuntivo': ['sepa', 'sepas', 'sepa', 'sepamos', 'sepáis', 'sepan'],
    },
    'dar': {
        'presente': ['doy', 'das', 'da', 'damos', 'dais', 'dan'],
        'pretérito': ['di', 'diste', 'dio', 'dimos', 'disteis', 'dieron'],
        'subjuntivo': ['dé', 'des', 'dé', 'demos', 'deis', 'den'],
    },
    'ver': {
        'presente': ['veo', 'ves', 've', 'vemos', 'veis', 'ven'],
        'pretérito': ['vi', 'viste', 'vio', 'vimos', 'visteis', 'vieron'],
        'imperfecto': ['veía', 'veías', 'veía', 'veíamos', 'veíais', 'veían'],
        'subjuntivo': ['vea', 'veas', 'vea', 'veamos', 'veáis', 'vean'],
    },
    'poder': {
        'presente': ['puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden'],
        'pretérito': ['pude', 'pudiste', 'pudo', 'pudimos', 'pudisteis', 'pudieron'],
        'futuro': ['podré', 'podrás', 'podrá', 'podremos', 'podréis', 'podrán'],
        'condicional': ['podría', 'podrías', 'podría', 'podríamos', 'podríais', 'podrían'],
        'subjuntivo': ['pueda', 'puedas', 'pueda', 'podamos', 'podáis', 'puedan'],
    },
    'querer': {
        'presente': ['quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren'],
        'pretérito': ['quise', 'quisiste', 'quiso', 'quisimos', 'quisisteis', 'quisieron'],
        'futuro': ['querré', 'querrás', 'querrá', 'querremos', 'querréis', 'querrán'],
        'condicional': ['querría', 'querrías', 'querría', 'querríamos', 'querríais', 'querrían'],
        'subjuntivo': ['quiera', 'quieras', 'quiera', 'queramos', 'queráis', 'quieran'],
    },
    'traer': {
        'presente': ['traigo', 'traes', 'trae', 'traemos', 'traéis', 'traen'],
        'pretérito': ['traje', 'trajiste', 'trajo', 'trajimos', 'trajisteis', 'trajeron'],
        'subjuntivo': ['traiga', 'traigas', 'traiga', 'traigamos', 'traigáis', 'traigan'],
    },
    'caer': {
        'presente': ['caigo', 'caes', 'cae', 'caemos', 'caéis', 'caen'],
        'pretérito': ['caí', 'caíste', 'cayó', 'caímos', 'caísteis', 'cayeron'],
        'subjuntivo': ['caiga', 'caigas', 'caiga', 'caigamos', 'caigáis', 'caigan'],
    },
    'oír': {
        'presente': ['oigo', 'oyes', 'oye', 'oímos', 'oís', 'oyen'],
        'pretérito': ['oí', 'oíste', 'oyó', 'oímos', 'oísteis', 'oyeron'],
        'subjuntivo': ['oiga', 'oigas', 'oiga', 'oigamos', 'oigáis', 'oigan'],
    },
    'conducir': {
        'presente': ['conduzco', 'conduces', 'conduce', 'conducimos', 'conducís', 'conducen'],
        'pretérito': ['conduje', 'condujiste', 'condujo', 'condujimos', 'condujisteis', 'condujeron'],
        'subjuntivo': ['conduzca', 'conduzcas', 'conduzca', 'conduzcamos', 'conduzcáis', 'conduzcan'],
    },
    'conocer': {
        'presente': ['conozco', 'conoces', 'conoce', 'conocemos', 'conocéis', 'conocen'],
        'subjuntivo': ['conozca', 'conozcas', 'conozca', 'conozcamos', 'conozcáis', 'conozcan'],
    },
    'parecer': {
        'presente': ['parezco', 'pareces', 'parece', 'parecemos', 'parecéis', 'parecen'],
        'subjuntivo': ['parezca', 'parezcas', 'parezca', 'parezcamos', 'parezcáis', 'parezcan'],
    },
    'nacer': {
        'presente': ['nazco', 'naces', 'nace', 'nacemos', 'nacéis', 'nacen'],
        'subjuntivo': ['nazca', 'nazcas', 'nazca', 'nazcamos', 'nazcáis', 'nazcan'],
    },
    'crecer': {
        'presente': ['crezco', 'creces', 'crece', 'crecemos', 'crecéis', 'crecen'],
        'subjuntivo': ['crezca', 'crezcas', 'crezca', 'crezcamos', 'crezcáis', 'crezcan'],
    },
    'producir': {
        'presente': ['produzco', 'produces', 'produce', 'producimos', 'producís', 'producen'],
        'pretérito': ['produje', 'produjiste', 'produjo', 'produjimos', 'produjisteis', 'produjeron'],
        'subjuntivo': ['produzca', 'produzcas', 'produzca', 'produzcamos', 'produzcáis', 'produzcan'],
    },
    'traducir': {
        'presente': ['traduzco', 'traduces', 'traduce', 'traducimos', 'traducís', 'traducen'],
        'pretérito': ['traduje', 'tradujiste', 'tradujo', 'tradujimos', 'tradujisteis', 'tradujeron'],
        'subjuntivo': ['traduzca', 'traduzcas', 'traduzca', 'traduzcamos', 'traduzcáis', 'traduzcan'],
    },
    'caber': {
        'presente': ['quepo', 'cabes', 'cabe', 'cabemos', 'cabéis', 'caben'],
        'pretérito': ['cupe', 'cupiste', 'cupo', 'cupimos', 'cupisteis', 'cupieron'],
        'futuro': ['cabré', 'cabrás', 'cabrá', 'cabremos', 'cabréis', 'cabrán'],
        'condicional': ['cabría', 'cabrías', 'cabría', 'cabríamos', 'cabríais', 'cabrían'],
        'subjuntivo': ['quepa', 'quepas', 'quepa', 'quepamos', 'quepáis', 'quepan'],
    },
    'valer': {
        'presente': ['valgo', 'vales', 'vale', 'valemos', 'valéis', 'valen'],
        'futuro': ['valdré', 'valdrás', 'valdrá', 'valdremos', 'valdréis', 'valdrán'],
        'condicional': ['valdría', 'valdrías', 'valdría', 'valdríamos', 'valdríais', 'valdrían'],
        'subjuntivo': ['valga', 'valgas', 'valga', 'valgamos', 'valgáis', 'valgan'],
    },
}

# Verbs that conjugate like another verb (with a prefix)
# Format: {verb: (base_irregular, prefix_to_add)}
COMPOUNDS = {
    'obtener': ('tener', 'ob'),
    'mantener': ('tener', 'man'),
    'contener': ('tener', 'con'),
    'detener': ('tener', 'de'),
    'sostener': ('tener', 'sos'),
    'retener': ('tener', 're'),
    'entretener': ('tener', 'entre'),
    'deshacer': ('hacer', 'des'),
    'rehacer': ('hacer', 're'),
    'satisfacer': ('hacer', 'satis'),  # satisfacer → satisfago, etc.
    'componer': ('poner', 'com'),
    'disponer': ('poner', 'dis'),
    'exponer': ('poner', 'ex'),
    'imponer': ('poner', 'im'),
    'oponer': ('poner', 'o'),
    'proponer': ('poner', 'pro'),
    'reponer': ('poner', 're'),
    'suponer': ('poner', 'su'),
    'convenir': ('venir', 'con'),
    'prevenir': ('venir', 'pre'),
    'intervenir': ('venir', 'inter'),
    'provenir': ('venir', 'pro'),
    'predecir': ('decir', 'pre'),
    'contradecir': ('decir', 'contra'),
    'bendecir': ('decir', 'ben'),
    'maldecir': ('decir', 'mal'),
    'distraer': ('traer', 'dis'),
    'atraer': ('traer', 'a'),
    'extraer': ('traer', 'ex'),
    'sustraer': ('traer', 'sus'),
    'contraer': ('traer', 'con'),
    'devolver': ('volver', 'de'),
    'resolver': ('volver', 're'),  # actually resuelvo
    'envolver': ('volver', 'en'),
    'revolver': ('volver', 're'),
    'reducir': ('conducir', 're'),
    'introducir': ('conducir', 'intro'),
    'reproducir': ('conducir', 'repro'),
    'deducir': ('conducir', 'de'),
    'seducir': ('conducir', 'se'),
    'reconocer': ('conocer', 're'),
    'desconocer': ('conocer', 'des'),
    'aparecer': ('parecer', 'a'),
    'desaparecer': ('parecer', 'desa'),
    'pertenecer': ('parecer', 'pertene'),  # -ecer pattern
    'ofrecer': ('parecer', 'ofre'),
    'agradecer': ('parecer', 'agrade'),
    'merecer': ('parecer', 'mere'),
    'establecer': ('parecer', 'establ'),
    'favorecer': ('parecer', 'favore'),
    'fortalecer': ('parecer', 'fortal'),
    'enriquecer': ('parecer', 'enrique'),
    'empobrecer': ('parecer', 'empobre'),
    'oscurecer': ('parecer', 'oscure'),
    'amanecer': ('parecer', 'amane'),
    'atardecer': ('parecer', 'atarde'),
    'envejecer': ('parecer', 'enveje'),
    'humedecer': ('parecer', 'humede'),
    'obedecer': ('parecer', 'obede'),
    'padecer': ('parecer', 'pade'),
    'permanecer': ('parecer', 'permane'),
    'prevalecer': ('parecer', 'prevale'),
    'carecer': ('parecer', 'care'),
    'complacer': ('parecer', 'compla'),  # actually -acer
    'renacer': ('nacer', 're'),
}

# ============================================================
# -go VERBS (yo form irregularity in presente + subjuntivo)
# ============================================================
GO_VERBS = {
    # verb: presente yo form (subjuntivo built from it)
    'tener': 'tengo', 'venir': 'vengo', 'poner': 'pongo',
    'salir': 'salgo', 'hacer': 'hago', 'decir': 'digo',
    'traer': 'traigo', 'caer': 'caigo', 'oír': 'oigo',
    'valer': 'valgo',
}

# ============================================================
# FUTURO / CONDICIONAL irregular stems
# ============================================================
FUTURE_STEMS = {
    'tener': 'tendr', 'venir': 'vendr', 'poner': 'pondr',
    'salir': 'saldr', 'haber': 'habr', 'saber': 'sabr',
    'poder': 'podr', 'querer': 'querr', 'hacer': 'har',
    'decir': 'dir', 'caber': 'cabr', 'valer': 'valdr',
}


# ============================================================
# MAIN CONJUGATION FUNCTION
# ============================================================
def get_verb_group(infinitive):
    """Return 'ar', 'er', or 'ir'."""
    clean = infinitive.rstrip('se')  # handle reflexive
    if clean.endswith('ar'):
        return 'ar'
    elif clean.endswith('er') or clean == 'ver':
        return 'er'
    elif clean.endswith('ir') or clean.endswith('ír'):
        return 'ir'
    return None

def get_stem(infinitive, group):
    """Get the stem by removing the -ar/-er/-ir ending."""
    if infinitive.endswith('ír'):
        return infinitive[:-2]
    if infinitive.endswith('irse') or infinitive.endswith('arse') or infinitive.endswith('erse'):
        return infinitive[:-4]
    return infinitive[:-2]

def conjugate(infinitive):
    """
    Conjugate a Spanish verb.
    Returns dict: {tense: {person: form}} for 6 tenses × 6 persons.
    """
    # Strip reflexive for conjugation purposes
    is_reflexive = infinitive.endswith('se')
    base_inf = infinitive[:-2] if is_reflexive else infinitive

    # Check if this is a compound of an irregular verb
    compound_prefix = None
    base_irregular = None
    if base_inf in COMPOUNDS:
        base_irregular, compound_prefix = COMPOUNDS[base_inf]

    group = get_verb_group(base_inf)
    if not group:
        return {}

    stem = get_stem(base_inf, group)
    result = {}
    tenses = ['presente', 'pretérito', 'imperfecto', 'futuro', 'condicional', 'subjuntivo']

    for tense in tenses:
        forms = [None] * 6

        # 1. Check full irregular override
        irr_verb = base_inf
        if base_irregular and base_irregular in IRREGULARS:
            irr = IRREGULARS[base_irregular]
            if tense in irr:
                base_forms = irr[tense]
                # Apply prefix: compound_prefix + base_form, but we need to handle
                # the base verb's stem being replaced
                # For tener→tengo, obtener→obtengo: prefix 'ob' + 'tengo'
                # Actually for compounds, the base irregular's root is replaced
                # So we strip the base verb from the form and prepend our prefix
                for i, f in enumerate(base_forms):
                    forms[i] = compound_prefix + f
                result[tense] = dict(zip(PERSONS, forms))
                continue
        elif base_inf in IRREGULARS:
            irr = IRREGULARS[base_inf]
            if tense in irr:
                result[tense] = dict(zip(PERSONS, irr[tense]))
                continue

        # 2. Future/conditional with irregular stems
        if tense in ('futuro', 'condicional'):
            fut_stem = None
            if base_inf in FUTURE_STEMS:
                fut_stem = FUTURE_STEMS[base_inf]
            elif base_irregular and base_irregular in FUTURE_STEMS:
                # Compound: replace base's stem with compound prefix
                base_fut = FUTURE_STEMS[base_irregular]
                # e.g., tener→tendr, obtener→obtendr
                fut_stem = compound_prefix + base_fut

            if fut_stem:
                endings = REGULAR[tense]['ar']  # future/conditional endings are same for all
                for i, ending in enumerate(endings):
                    forms[i] = fut_stem + ending
                result[tense] = dict(zip(PERSONS, forms))
                continue

            # Regular future/conditional: infinitive + endings
            endings = REGULAR[tense][group]
            for i, ending in enumerate(endings):
                forms[i] = base_inf + ending
            result[tense] = dict(zip(PERSONS, forms))
            continue

        # 3. Regular conjugation with stem changes and spelling fixes
        endings = REGULAR[tense][group]
        sc_type = STEM_CHANGERS.get(base_inf)

        for i, ending in enumerate(endings):
            s = stem

            # Apply stem changes (presente: all except nosotros[3]/vosotros[4])
            if sc_type and tense == 'presente' and i not in (3, 4):
                s = apply_stem_change(s, sc_type)
            # Subjuntivo stem changes
            elif sc_type and tense == 'subjuntivo':
                if i not in (3, 4):
                    s = apply_stem_change(s, sc_type)
                elif group == 'ir' and sc_type in ('e>ie', 'e>i'):
                    # -ir stem changers: nosotros/vosotros get e→i in subjuntivo
                    s = apply_stem_change(s, 'e>i')
                elif group == 'ir' and sc_type == 'o>ue':
                    # dormir/morir: nosotros/vosotros get o→u in subjuntivo
                    idx = s.rfind('o')
                    if idx >= 0:
                        s = s[:idx] + 'u' + s[idx+1:]

            # Spelling changes
            if tense == 'pretérito' and i == 0:  # yo
                s = spelling_fix_pretérito_yo(s, group)
            if tense == 'subjuntivo':
                s = spelling_fix_subjuntivo(s, group)

            # -go verbs: yo presente irregularity
            if tense == 'presente' and i == 0:
                if base_inf in GO_VERBS:
                    forms[i] = GO_VERBS[base_inf]
                    continue
                elif base_irregular and base_irregular in GO_VERBS:
                    forms[i] = compound_prefix + GO_VERBS[base_irregular]
                    continue
                # -cer/-cir → -zco pattern (not in full IRREGULARS)
                if base_inf.endswith('cer') or base_inf.endswith('cir'):
                    if not base_inf.endswith('hacer') and base_inf not in IRREGULARS:
                        forms[i] = s[:-1] + 'zco'
                        continue

            forms[i] = s + ending

        result[tense] = dict(zip(PERSONS, forms))

    return result


def conjugate_to_cards(infinitive, english='', rank=9999):
    """
    Generate study cards for a verb.
    Returns list of card dicts with frequency rank for ordering.
    """
    forms = conjugate(infinitive)
    if not forms:
        return []

    cards = []
    tense_order = ['presente', 'pretérito', 'imperfecto', 'futuro', 'condicional', 'subjuntivo']
    # Tense priority: presente first (most useful), then past tenses, then rest
    tense_priority = {
        'presente': 0, 'pretérito': 1, 'imperfecto': 2,
        'futuro': 3, 'condicional': 4, 'subjuntivo': 5
    }

    for tense in tense_order:
        if tense not in forms:
            continue
        for pi, person in enumerate(PERSONS):
            form = forms[tense].get(person)
            if form:
                # Sort key: verb frequency first, then tense priority, then person
                sort_key = rank * 100 + tense_priority.get(tense, 9) * 10 + pi
                cards.append({
                    'verb': infinitive,
                    'verbEn': english,
                    'tense': tense,
                    'person': person,
                    'form': form,
                    'rank': rank,
                    'sortKey': sort_key,
                    'id': f"{infinitive}-{tense}-{person}"
                })
    return cards
