/* ============================================================
   SpanishKB Study PWA — App Logic
   Adaptive deck engine with 6 practice modes + grammar reference
   ============================================================ */
(function () {
  'use strict';

  // ============================================================
  // CONSTANTS & CONFIG
  // ============================================================
  var PREFIX = 'spanishkb';
  var DARK_KEY = PREFIX + '-dark';
  var STREAK_KEY = PREFIX + '-streak';
  var SETTINGS_KEY = PREFIX + '-settings';

  var MODE_CONFIG = {
    vocab: {
      namespace: 'vocab',
      label: 'Vocab Flash',
      icon: '\uD83D\uDCDA',
      defaultDeck: 20,
      getId: function (item) { return String(item.rank); },
      getItems: function (data) { return data.words || []; }
    },
    patterns: {
      namespace: 'patterns',
      label: 'Verb Patterns',
      icon: '\uD83D\uDD24',
      defaultDeck: 15,
      getId: function (item) { return item.id; },
      getItems: function (data) { return data.conjugationPatterns || []; }
    },
    irregulars: {
      namespace: 'irregulars',
      label: 'Irregular Verbs',
      icon: '\u26A1',
      defaultDeck: 15,
      getId: function (item) { return item.id; },
      getItems: function (data) { return data.conjugationIrregulars || []; }
    },
    medvocab: {
      namespace: 'medvocab',
      label: 'Medical Vocab',
      icon: '\uD83C\uDFE5',
      defaultDeck: 15,
      getId: function (item) { return item.es; },
      getItems: function (data) { return data.medicalVocab || []; }
    },
    medphrase: {
      namespace: 'medphrase',
      label: 'Medical Phrases',
      icon: '\uD83D\uDCAC',
      defaultDeck: 15,
      getId: function (item) { return item.es; },
      getItems: function (data) { return data.medicalPhrases || []; }
    },
    expressions: {
      namespace: 'expr',
      label: 'Expresiones',
      icon: '\uD83D\uDDE3\uFE0F',
      defaultDeck: 15,
      getId: function (item) { return item.es; },
      getItems: function (data) { return data.expressions || []; }
    }
  };

  var DEFAULT_SETTINGS = {
    deckSize: 20,
    masteryThreshold: 3,
    showType: true,
    showExample: true
  };

  // ============================================================
  // STATE
  // ============================================================
  var DATA = null;
  var settings = null;
  var session = null;
  var engines = {};
  var currentView = 'home';

  // ============================================================
  // UTILITIES
  // ============================================================
  function lsGet(key) {
    try { return JSON.parse(localStorage.getItem(key)); }
    catch (e) { return null; }
  }

  function lsSet(key, val) {
    localStorage.setItem(key, JSON.stringify(val));
  }

  function today() {
    return new Date().toISOString().slice(0, 10);
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  var FREQ_LABELS = { 1: ' \u2022 Every patient', 2: ' \u2022 Most shifts', 3: ' \u2022 Regular', 4: ' \u2022 Specialized' };
  function freqLabel(freq) {
    return FREQ_LABELS[freq] || '';
  }

  // ============================================================
  // DECK ENGINE
  // ============================================================
  function getEngine(mode) {
    if (!engines[mode]) {
      engines[mode] = createEngine(mode);
    }
    return engines[mode];
  }

  function createEngine(mode) {
    var cfg = MODE_CONFIG[mode];
    var ns = PREFIX + '-' + cfg.namespace;
    var items = cfg.getItems(DATA);

    // Build lookup tables
    var itemById = {};
    var itemList = [];
    items.forEach(function (item, idx) {
      var id = cfg.getId(item, idx);
      itemById[id] = item;
      itemList.push({ id: id, item: item, idx: idx });
    });

    // Load persisted state
    var deck     = lsGet(ns + '-deck') || {};
    var mastered = lsGet(ns + '-mastered') || {};
    var queueIdx = lsGet(ns + '-queueIdx');
    if (queueIdx === null) queueIdx = 0;
    var bumped   = lsGet(ns + '-bumped') || [];

    // Prune stale IDs that no longer exist in data (after re-export)
    Object.keys(deck).forEach(function (id) {
      if (!itemById[id]) delete deck[id];
    });
    Object.keys(mastered).forEach(function (id) {
      if (!itemById[id]) delete mastered[id];
    });

    var engine = {
      mode: mode, cfg: cfg, ns: ns,
      items: items, itemById: itemById, itemList: itemList,
      deck: deck, mastered: mastered, queueIdx: queueIdx, bumped: bumped
    };

    ensureDeckFull(engine);
    saveEngine(engine);
    return engine;
  }

  function saveEngine(engine) {
    var ns = engine.ns;
    lsSet(ns + '-deck', engine.deck);
    lsSet(ns + '-mastered', engine.mastered);
    lsSet(ns + '-queueIdx', engine.queueIdx);
    lsSet(ns + '-bumped', engine.bumped);
  }

  function ensureDeckFull(engine) {
    var targetSize = settings.deckSize || engine.cfg.defaultDeck;
    var count = Object.keys(engine.deck).length;

    while (count < targetSize) {
      // Priority 1: bumped items (preserve previous progress)
      if (engine.bumped.length > 0) {
        var b = engine.bumped.shift();
        if (!engine.deck[b.id] && !engine.mastered[b.id] && engine.itemById[b.id]) {
          engine.deck[b.id] = {
            streak: b.streak || 0,
            lastSeen: b.lastSeen || null,
            timesRated: b.timesRated || 0
          };
          count++;
          continue;
        }
        continue; // skip invalid bumped item, try next
      }

      // Priority 2: next item from frequency queue
      if (engine.queueIdx < engine.itemList.length) {
        var entry = engine.itemList[engine.queueIdx];
        engine.queueIdx++;
        if (!engine.deck[entry.id] && !engine.mastered[entry.id]) {
          engine.deck[entry.id] = { streak: 0, lastSeen: null, timesRated: 0 };
          count++;
        }
        continue;
      }

      break; // no more items available
    }
  }

  function getEngineStats(engine) {
    var total = engine.itemList.length;
    var masteredCount = Object.keys(engine.mastered).length;
    var deckCount = Object.keys(engine.deck).length;
    return {
      total: total,
      mastered: masteredCount,
      deck: deckCount,
      unseen: Math.max(0, total - masteredCount - deckCount)
    };
  }

  // ============================================================
  // SESSION
  // ============================================================
  function buildSession(mode) {
    var engine = getEngine(mode);
    var cards = [];

    // Add all active deck items
    Object.keys(engine.deck).forEach(function (id) {
      var item = engine.itemById[id];
      if (item) {
        cards.push({ id: id, item: item, isMasteryCheck: false });
      }
    });

    // Add mastery check items (5% of deck size, min 1 if any mastered)
    var masteredIds = Object.keys(engine.mastered);
    var checksTarget = Math.max(1, Math.round((settings.deckSize || 20) * 0.05));
    var checksCount = Math.min(checksTarget, masteredIds.length);
    var shuffledMastered = shuffle(masteredIds);
    for (var i = 0; i < checksCount; i++) {
      var id = shuffledMastered[i];
      var item = engine.itemById[id];
      if (item) {
        cards.push({ id: id, item: item, isMasteryCheck: true });
      }
    }

    return {
      mode: mode,
      cards: shuffle(cards),
      currentIndex: 0,
      ratings: {},
      flipped: false,
      startTime: Date.now()
    };
  }

  function processSessionResults() {
    // Ratings were already processed incrementally in processOneRating().
    // This function now just tallies results for the summary screen.
    if (!session) return { promoted: [], demoted: [] };

    var engine = getEngine(session.mode);
    var promoted = [];
    var demoted = [];

    // Check which items were promoted/demoted during this session
    var cardMap = {};
    session.cards.forEach(function (c) { cardMap[c.id] = c; });

    Object.keys(session.ratings).forEach(function (id) {
      var rating = session.ratings[id];
      var card = cardMap[id];
      if (!card) return;

      if (card.isMasteryCheck && rating === 'dont-know') {
        demoted.push(id);
      } else if (!card.isMasteryCheck && rating === 'know' && engine.mastered[id]) {
        promoted.push(id);
      }
    });

    return { promoted: promoted, demoted: demoted };
  }

  // ============================================================
  // STREAK
  // ============================================================
  function getStreak() {
    var data = lsGet(STREAK_KEY) || { count: 0, lastDate: null };
    var t = today();
    if (data.lastDate === t) return data;

    var yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (data.lastDate === yesterday) return data;

    // Streak broken
    return { count: 0, lastDate: data.lastDate };
  }

  function updateStreak() {
    var streak = getStreak();
    var t = today();
    if (streak.lastDate !== t) {
      streak.count++;
      streak.lastDate = t;
      lsSet(STREAK_KEY, streak);
    }
    return streak;
  }

  // ============================================================
  // NAVIGATION
  // ============================================================
  function showView(name) {
    currentView = name;

    // Toggle view visibility
    document.querySelectorAll('.view').forEach(function (v) {
      v.classList.remove('active');
    });
    var el = document.getElementById('view-' + name);
    if (el) el.classList.add('active');

    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.view === name);
    });

    // Update topbar
    var backBtn = document.getElementById('topbar-back');
    var title = document.getElementById('topbar-title');

    if (name === 'home') {
      backBtn.style.display = 'none';
      title.textContent = 'SpanishKB Study';
    } else if (name === 'practice') {
      backBtn.style.display = '';
      title.textContent = session ? MODE_CONFIG[session.mode].label : '';
    } else if (name === 'summary') {
      backBtn.style.display = '';
      title.textContent = 'Session Complete';
    } else if (name === 'progress') {
      backBtn.style.display = 'none';
      title.textContent = 'Progress';
    } else if (name === 'settings') {
      backBtn.style.display = 'none';
      title.textContent = 'Settings';
    }

    // Render view content
    if (name === 'home') renderHome();
    else if (name === 'progress') renderProgress();
    else if (name === 'settings') renderSettings();
    else if (name === 'grammar') renderGrammar();
  }

  function goHome() {
    if (session && currentView === 'practice') {
      if (!confirm('Leave this session? Your ratings so far will be lost.')) return;
      session = null;
    }
    showView('home');
  }

  // ============================================================
  // HOME VIEW
  // ============================================================
  function renderHome() {
    // Greeting
    var hour = new Date().getHours();
    var greet = hour < 12 ? '\u00A1Buenos d\u00EDas!'
              : hour < 18 ? '\u00A1Buenas tardes!'
              : '\u00A1Buenas noches!';
    document.getElementById('home-greeting').textContent = greet;

    // Streak
    var streak = getStreak();
    var streakEl = document.getElementById('home-streak');
    streakEl.textContent = streak.count > 0
      ? '\uD83D\uDD25 ' + streak.count + '-day streak'
      : 'Start your streak today!';

    // Mode card progress counts
    var modeMap = {
      vocab:       'home-vocab-progress',
      patterns:    'home-patterns-progress',
      irregulars:  'home-irregulars-progress',
      medvocab:    'home-medvocab-progress',
      medphrase:   'home-medphrase-progress',
      expressions: 'home-expr-progress'
    };

    Object.keys(modeMap).forEach(function (mode) {
      var el = document.getElementById(modeMap[mode]);
      if (!el) return;

      var items = MODE_CONFIG[mode].getItems(DATA);
      if (!items || items.length === 0) {
        el.textContent = 'Coming soon';
        return;
      }

      var engine = getEngine(mode);
      var stats = getEngineStats(engine);
      el.textContent = stats.mastered + ' / ' + stats.total.toLocaleString();
    });
  }

  // ============================================================
  // PRACTICE VIEW — Start, Render, Flip, Rate
  // ============================================================
  function startMode(mode) {
    var cfg = MODE_CONFIG[mode];
    var items = cfg.getItems(DATA);

    if (!items || items.length === 0) {
      alert('No cards available for ' + cfg.label +
            ' yet. Add content to your vault and re-export!');
      return;
    }

    session = buildSession(mode);

    if (session.cards.length === 0) {
      // All mastered and no mastery checks
      alert('\uD83C\uDF89 You\'ve mastered everything in ' + cfg.label +
            '! Amazing work! Adjust settings or wait for new content.');
      session = null;
      return;
    }

    showView('practice');
    renderPractice();
  }

  function renderPractice() {
    if (!session) return;

    var card = session.cards[session.currentIndex];
    var mode = session.mode;

    // Header
    document.getElementById('practice-mode-label').textContent =
      MODE_CONFIG[mode].label;
    document.getElementById('practice-counter').textContent =
      (session.currentIndex + 1) + ' / ' + session.cards.length;

    // Snap back to front instantly (no animation) to prevent flash of previous answer
    var cardInner = document.getElementById('card-inner');
    cardInner.style.transition = 'none';
    cardInner.classList.remove('flipped');
    // Force browser to apply the style change before re-enabling transition
    void cardInner.offsetHeight;
    cardInner.style.transition = '';
    session.flipped = false;

    // Hide rating buttons
    document.getElementById('rating-row').style.display = 'none';

    // Mastery check badge
    var badge = document.getElementById('card-badge');
    if (card.isMasteryCheck) {
      badge.style.display = '';
      badge.textContent = '\u2B50 Mastery Check';
    } else {
      badge.style.display = 'none';
    }

    // Render card faces
    renderCardFront(mode, card);
    renderCardBack(mode, card);
  }

  function renderCardFront(mode, card) {
    var item = card.item;
    var prompt = document.getElementById('card-prompt');
    var hint = document.getElementById('card-hint');

    if (mode === 'vocab') {
      prompt.textContent = item.en;
      hint.textContent = settings.showType ? item.type : '';

    } else if (mode === 'patterns') {
      prompt.innerHTML =
        '<span style="font-size:22px;color:var(--accent)">' +
        escapeHtml(item.group) + '</span><br>' +
        '<span style="font-size:18px">' +
        escapeHtml(item.tense) + ' \u00B7 ' + escapeHtml(item.person) + '</span>';
      hint.textContent = 'What\u2019s the ending?';

    } else if (mode === 'irregulars') {
      prompt.innerHTML =
        '<span style="font-size:18px;color:var(--text-muted)">' +
        escapeHtml(item.verbEn || item.verb) + '</span><br>' +
        escapeHtml(item.tense) + ' \u00B7 ' + escapeHtml(item.person);
      hint.textContent = item.verb;

    } else if (mode === 'medvocab') {
      prompt.textContent = item.en;
      hint.textContent = (item.category || '') + freqLabel(item.freq);

    } else if (mode === 'medphrase') {
      prompt.textContent = item.en;
      hint.textContent = (item.category || '') + freqLabel(item.freq);

    } else if (mode === 'expressions') {
      prompt.textContent = item.en;
      hint.textContent = (item.category || '') + freqLabel(item.freq);
    }
  }

  function renderCardBack(mode, card) {
    var item = card.item;
    var answer = document.getElementById('card-answer');
    var detail = document.getElementById('card-detail');
    var example = document.getElementById('card-example');

    if (mode === 'vocab') {
      answer.textContent = item.es;
      detail.textContent = item.en;
      if (settings.showExample && item.ex) {
        example.textContent = item.ex;
        example.style.display = '';
      } else {
        example.textContent = '';
        example.style.display = 'none';
      }

    } else if (mode === 'patterns') {
      answer.innerHTML = '<span style="font-size:28px;color:var(--accent)">' +
                         escapeHtml(item.ending) + '</span>';
      detail.textContent = item.example;
      example.textContent = item.exampleEn || '';
      example.style.display = item.exampleEn ? '' : 'none';

    } else if (mode === 'irregulars') {
      answer.textContent = item.form;
      detail.textContent = item.verb + ' \u00B7 ' + item.tense +
                           ' \u00B7 ' + item.person;
      example.textContent = '';
      example.style.display = 'none';

    } else if (mode === 'medvocab') {
      answer.textContent = item.es;
      detail.textContent = item.en;
      if (item.category) {
        example.textContent = item.category;
        example.style.display = '';
      } else {
        example.textContent = '';
        example.style.display = 'none';
      }

    } else if (mode === 'medphrase') {
      answer.textContent = item.es;
      detail.textContent = item.en;
      if (item.source) {
        example.textContent = 'Source: ' + item.source;
        example.style.display = '';
      } else {
        example.textContent = '';
        example.style.display = 'none';
      }

    } else if (mode === 'expressions') {
      answer.textContent = item.es;
      detail.textContent = item.en;
      if (item.category) {
        example.textContent = item.category;
        example.style.display = '';
      } else {
        example.textContent = '';
        example.style.display = 'none';
      }
    }
  }

  function flipCard() {
    if (!session || session.flipped) return;
    session.flipped = true;
    document.getElementById('card-inner').classList.add('flipped');
    document.getElementById('rating-row').style.display = 'flex';
  }

  function rate(rating) {
    if (!session || !session.flipped) return;

    var card = session.cards[session.currentIndex];
    session.ratings[card.id] = rating;

    // Process this rating IMMEDIATELY so progress is never lost
    processOneRating(session.mode, card, rating);

    // Advance to next card
    session.currentIndex++;

    if (session.currentIndex >= session.cards.length) {
      finishSession();
    } else {
      renderPractice();
    }
  }

  function processOneRating(mode, card, rating) {
    var engine = getEngine(mode);
    var id = card.id;
    var threshold = settings.masteryThreshold || 3;

    if (card.isMasteryCheck) {
      if (rating === 'dont-know') {
        delete engine.mastered[id];
        engine.deck[id] = { streak: 0, lastSeen: today(), timesRated: 1 };
      } else if (rating === 'know' && engine.mastered[id]) {
        engine.mastered[id].lastChecked = today();
        engine.mastered[id].checkStreak =
          (engine.mastered[id].checkStreak || 0) + 1;
      }
    } else {
      if (!engine.deck[id]) return;
      engine.deck[id].lastSeen = today();
      engine.deck[id].timesRated = (engine.deck[id].timesRated || 0) + 1;

      if (rating === 'know') {
        engine.deck[id].streak = (engine.deck[id].streak || 0) + 1;
        if (engine.deck[id].streak >= threshold) {
          engine.mastered[id] = {
            masteredDate: today(),
            lastChecked: null,
            checkStreak: 0
          };
          delete engine.deck[id];
          // Immediately fill the empty slot
          ensureDeckFull(engine);
        }
      } else if (rating === 'dont-know') {
        engine.deck[id].streak = 0;
      }
    }

    saveEngine(engine);
  }

  // ============================================================
  // SESSION FINISH & SUMMARY
  // ============================================================
  function finishSession() {
    // Process while session is still alive
    var results = processSessionResults();
    var streak = updateStreak();

    // Render summary (still needs session data)
    renderSummary(results, streak);
    showView('summary');

    // Now clear session
    session = null;
  }

  function renderSummary(results, streak) {
    var container = document.getElementById('summary-content');
    var ratings = session.ratings;
    var mode = session.mode;

    var total = Object.keys(ratings).length;
    var knowCount = 0, practiceCount = 0, dontKnowCount = 0;
    Object.keys(ratings).forEach(function (id) {
      if (ratings[id] === 'know') knowCount++;
      else if (ratings[id] === 'need-practice') practiceCount++;
      else if (ratings[id] === 'dont-know') dontKnowCount++;
    });

    var html = '<div class="summary-header">' +
      '<h2>\u00A1Bien hecho! \uD83C\uDF89</h2>' +
      '<p style="color:var(--text-muted)">' + MODE_CONFIG[mode].label + ' Session</p>' +
      '</div>';

    html += '<div class="summary-stat">' +
      '<span class="summary-stat-label">Cards Reviewed</span>' +
      '<span class="summary-stat-value">' + total + '</span></div>';

    html += '<div class="summary-stat">' +
      '<span class="summary-stat-label">\u2713 Know</span>' +
      '<span class="summary-stat-value green">' + knowCount + '</span></div>';

    html += '<div class="summary-stat">' +
      '<span class="summary-stat-label">\u007E Need Practice</span>' +
      '<span class="summary-stat-value" style="color:var(--amber)">' + practiceCount + '</span></div>';

    html += '<div class="summary-stat">' +
      '<span class="summary-stat-label">\u2717 Don\'t Know</span>' +
      '<span class="summary-stat-value red">' + dontKnowCount + '</span></div>';

    // Newly mastered words
    if (results.promoted.length > 0) {
      var engine = getEngine(mode);
      html += '<div class="summary-words"><h3>\u2B50 Newly Mastered</h3>' +
        '<div class="summary-word-list">';
      results.promoted.forEach(function (id) {
        var item = engine.itemById[id];
        var label = item ? (item.es || item.form || id) : id;
        html += '<span class="summary-word-chip">' + escapeHtml(label) + '</span>';
      });
      html += '</div></div>';
    }

    // Demoted words (failed mastery check)
    if (results.demoted.length > 0) {
      var eng = getEngine(mode);
      html += '<div class="summary-words"><h3>\uD83D\uDCC9 Back for Review</h3>' +
        '<div class="summary-word-list">';
      results.demoted.forEach(function (id) {
        var item = eng.itemById[id];
        var label = item ? (item.es || item.form || id) : id;
        html += '<span class="summary-word-chip" ' +
          'style="background:var(--red-bg);color:var(--red)">' +
          escapeHtml(label) + '</span>';
      });
      html += '</div></div>';
    }

    // Encouragement
    var msgs = [
      '\u00A1Sigue as\u00ED! Keep going!',
      'Every card makes you stronger \uD83D\uDCAA',
      'Consistency is the key to fluency \uD83D\uDD11',
      '\u00A1T\u00FA puedes! You can do it!',
      'One session closer to fluency \uD83C\uDF1F',
      'Practice makes permanente \uD83E\uDDE0'
    ];
    html += '<div class="summary-encouragement">' +
      msgs[Math.floor(Math.random() * msgs.length)] + '</div>';

    if (streak.count > 0) {
      html += '<div class="summary-encouragement">\uD83D\uDD25 ' +
        streak.count + '-day streak!</div>';
    }

    html += '<button class="btn-primary" onclick="SKB.goHome()">Back to Home</button>';

    container.innerHTML = html;
  }

  // ============================================================
  // PROGRESS VIEW
  // ============================================================
  function renderProgress() {
    var container = document.getElementById('progress-content');
    var html = '';
    var hasAny = false;

    ['vocab', 'patterns', 'irregulars', 'medvocab', 'medphrase', 'expressions'].forEach(function (mode) {
      var cfg = MODE_CONFIG[mode];
      var items = cfg.getItems(DATA);
      if (!items || items.length === 0) return;
      hasAny = true;

      var engine = getEngine(mode);
      var stats = getEngineStats(engine);
      var pct = stats.total > 0
        ? Math.round((stats.mastered / stats.total) * 100) : 0;

      // SVG ring
      var circumference = Math.PI * 100; // 2 * PI * r(50)
      var offset = circumference * (1 - pct / 100);

      html += '<div class="progress-section">' +
        '<h2>' + cfg.icon + ' ' + cfg.label + '</h2>' +
        '<div class="progress-ring-container">' +
        '<svg width="120" height="120" viewBox="0 0 120 120">' +
        '<circle cx="60" cy="60" r="50" fill="none" stroke="var(--bg-elevated)" stroke-width="10"/>' +
        '<circle cx="60" cy="60" r="50" fill="none" stroke="var(--green)" stroke-width="10" ' +
        'stroke-dasharray="' + circumference.toFixed(1) + '" ' +
        'stroke-dashoffset="' + offset.toFixed(1) + '" ' +
        'transform="rotate(-90 60 60)" stroke-linecap="round"/>' +
        '<text x="60" y="55" text-anchor="middle" fill="var(--text)" ' +
        'font-size="22" font-weight="700">' + pct + '%</text>' +
        '<text x="60" y="72" text-anchor="middle" fill="var(--text-muted)" ' +
        'font-size="11">' + stats.mastered + ' / ' + stats.total.toLocaleString() + '</text>' +
        '</svg></div>';

      // Legend
      html += '<div class="progress-ring-label">' +
        '<span class="progress-dot mastered"></span> Mastered: ' + stats.mastered + '</div>' +
        '<div class="progress-ring-label">' +
        '<span class="progress-dot learning"></span> Learning: ' + stats.deck + '</div>' +
        '<div class="progress-ring-label">' +
        '<span class="progress-dot unseen"></span> Unseen: ' + stats.unseen + '</div>';

      // Progress bar
      var masteredPct = stats.total > 0 ? (stats.mastered / stats.total * 100) : 0;
      var learningPct = stats.total > 0 ? (stats.deck / stats.total * 100) : 0;
      html += '<div class="progress-bar-track" style="margin-top:12px">' +
        '<div style="display:flex;height:100%">' +
        '<div class="progress-bar-fill green" style="width:' + masteredPct.toFixed(1) + '%"></div>' +
        '<div class="progress-bar-fill amber" style="width:' + learningPct.toFixed(1) + '%"></div>' +
        '</div></div>';

      // Active deck word list (top 10)
      var deckIds = Object.keys(engine.deck);
      if (deckIds.length > 0) {
        html += '<div style="margin-top:12px;font-size:13px;color:var(--text-muted)">' +
          'Active deck (' + deckIds.length + ' cards):</div>' +
          '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">';
        deckIds.slice(0, 12).forEach(function (id) {
          var item = engine.itemById[id];
          var label = item ? (item.es || item.form || id) : id;
          var streak = engine.deck[id].streak || 0;
          var dots = '';
          for (var i = 0; i < (settings.masteryThreshold || 3); i++) {
            dots += i < streak
              ? '<span style="color:var(--green)">\u25CF</span>'
              : '<span style="color:var(--border)">\u25CB</span>';
          }
          html += '<div style="background:var(--bg-elevated);padding:4px 8px;' +
            'border-radius:6px;font-size:12px;display:flex;align-items:center;gap:4px">' +
            escapeHtml(label) + ' ' + dots + '</div>';
        });
        if (deckIds.length > 12) {
          html += '<div style="font-size:11px;color:var(--text-muted);padding:4px">' +
            '+ ' + (deckIds.length - 12) + ' more</div>';
        }
        html += '</div>';
      }

      html += '</div>'; // close progress-section
    });

    if (!hasAny) {
      html = '<div class="empty-state">' +
        '<div class="empty-icon">\uD83D\uDCCA</div>' +
        '<p>No data yet.<br>Start a practice session to track your progress!</p></div>';
    }

    container.innerHTML = html;
  }

  // ============================================================
  // SETTINGS VIEW
  // ============================================================
  function renderSettings() {
    var container = document.getElementById('settings-content');

    container.innerHTML =
      '<div class="setting-group">' +
      '<h2>Practice</h2>' +

      '<div class="setting-row">' +
      '<span class="setting-label">Deck Size</span>' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<input type="range" class="setting-slider" id="s-decksize" ' +
      'min="10" max="250" step="5" value="' + settings.deckSize + '" ' +
      'oninput="SKB.updateSetting(\'deckSize\', this.value)">' +
      '<span class="setting-value" id="v-decksize">' + settings.deckSize + '</span>' +
      '</div></div>' +

      '<div class="setting-row">' +
      '<span class="setting-label">Mastery Threshold</span>' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<input type="range" class="setting-slider" id="s-mastery" ' +
      'min="2" max="5" value="' + settings.masteryThreshold + '" ' +
      'oninput="SKB.updateSetting(\'masteryThreshold\', this.value)">' +
      '<span class="setting-value" id="v-mastery">' + settings.masteryThreshold + '</span>' +
      '</div></div>' +

      '<div class="setting-row">' +
      '<span class="setting-label">Mastery Checks / Session</span>' +
      '<span class="setting-value" id="v-checks">~' + Math.max(1, Math.round(settings.deckSize * 0.05)) + ' (5% of deck)</span>' +
      '</div>' +
      '</div>' +

      '<div class="setting-group">' +
      '<h2>Display</h2>' +

      '<div class="setting-row">' +
      '<span class="setting-label">Show Part of Speech</span>' +
      '<span class="setting-value" style="cursor:pointer" ' +
      'onclick="SKB.toggleSetting(\'showType\')" id="v-showtype">' +
      (settings.showType ? 'ON' : 'OFF') + '</span></div>' +

      '<div class="setting-row">' +
      '<span class="setting-label">Show Example Sentence</span>' +
      '<span class="setting-value" style="cursor:pointer" ' +
      'onclick="SKB.toggleSetting(\'showExample\')" id="v-showexample">' +
      (settings.showExample ? 'ON' : 'OFF') + '</span></div>' +
      '</div>' +

      '<div class="setting-group">' +
      '<h2>Data</h2>' +
      '<button class="btn-secondary" onclick="SKB.exportProgress()" style="margin-bottom:8px">' +
      '\uD83D\uDCE4 Export Progress</button>' +
      '<button class="btn-secondary" onclick="SKB.importProgress()">' +
      '\uD83D\uDCE5 Import Progress</button>' +
      '<input type="file" id="import-file" accept=".json" style="display:none" ' +
      'onchange="SKB.handleImportFile(this)">' +
      '<div id="backup-status" style="color:var(--accent);font-size:13px;margin-top:8px"></div>' +
      '</div>' +

      '<div class="setting-group">' +
      '<h2>Danger Zone</h2>' +
      '<button class="btn-danger" onclick="SKB.resetProgress()">' +
      'Reset All Progress</button>' +
      '</div>';
  }

  function updateSetting(key, value) {
    settings[key] = parseInt(value, 10);
    lsSet(SETTINGS_KEY, settings);

    var labels = {
      deckSize: 'v-decksize',
      masteryThreshold: 'v-mastery'
    };
    var el = document.getElementById(labels[key]);
    if (el) el.textContent = value;

    // Update mastery checks display when deck size changes
    if (key === 'deckSize') {
      var checksEl = document.getElementById('v-checks');
      if (checksEl) checksEl.textContent = '~' + Math.max(1, Math.round(value * 0.05)) + ' (5% of deck)';
    }
  }

  function toggleSetting(key) {
    settings[key] = !settings[key];
    lsSet(SETTINGS_KEY, settings);

    var labels = { showType: 'v-showtype', showExample: 'v-showexample' };
    var el = document.getElementById(labels[key]);
    if (el) el.textContent = settings[key] ? 'ON' : 'OFF';
  }

  function resetProgress() {
    if (!confirm('Reset ALL progress? This cannot be undone.')) return;
    if (!confirm('Are you absolutely sure? All mastered words and streaks will be lost.')) return;

    // Clear all per-mode localStorage
    Object.keys(MODE_CONFIG).forEach(function (mode) {
      var ns = PREFIX + '-' + MODE_CONFIG[mode].namespace;
      localStorage.removeItem(ns + '-deck');
      localStorage.removeItem(ns + '-mastered');
      localStorage.removeItem(ns + '-queueIdx');
      localStorage.removeItem(ns + '-bumped');
    });
    localStorage.removeItem(STREAK_KEY);

    // Reset in-memory engines
    engines = {};

    showView('home');
  }

  // ============================================================
  // PROGRESS EXPORT / IMPORT
  // ============================================================
  function exportProgress() {
    var backup = {};
    for (var i = 0; i < localStorage.length; i++) {
      var key = localStorage.key(i);
      if (key.startsWith(PREFIX)) {
        backup[key] = localStorage.getItem(key);
      }
    }
    var json = JSON.stringify(backup, null, 2);
    var blob = new Blob([json], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'spanishkb-progress-' + new Date().toISOString().slice(0, 10) + '.json';
    a.click();
    URL.revokeObjectURL(url);
    var status = document.getElementById('backup-status');
    if (status) status.textContent = '\u2705 Progress exported!';
  }

  function importProgress() {
    document.getElementById('import-file').click();
  }

  function handleImportFile(input) {
    var file = input.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function (e) {
      try {
        var backup = JSON.parse(e.target.result);
        var count = 0;
        Object.keys(backup).forEach(function (key) {
          if (key.startsWith(PREFIX)) {
            localStorage.setItem(key, backup[key]);
            count++;
          }
        });
        engines = {};  // Reset in-memory engines to pick up imported data
        var status = document.getElementById('backup-status');
        if (status) status.textContent = '\u2705 Imported ' + count + ' keys! Refreshing...';
        setTimeout(function () { location.reload(); }, 1000);
      } catch (err) {
        alert('Invalid backup file: ' + err.message);
      }
    };
    reader.readAsText(file);
    input.value = '';  // Reset so same file can be re-imported
  }

  // ============================================================
  // GRAMMAR REFERENCE VIEW
  // ============================================================
  function renderGrammar() {
    var container = document.getElementById('grammar-content');
    if (!container) return;

    if (!DATA || !DATA.grammarNotes || DATA.grammarNotes.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted)">No grammar notes found.</p>';
      return;
    }

    var html = '';
    DATA.grammarNotes.forEach(function (section) {
      html += '<div class="grammar-section">';
      html += '<h2>' + escapeHtml(section.title) + '</h2>';
      // Convert markdown to basic HTML
      html += markdownToHtml(section.content);
      html += '</div>';
    });
    container.innerHTML = html;
  }

  function markdownToHtml(md) {
    var lines = md.split('\n');
    var html = '';
    var inTable = false;
    var inList = false;

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];

      // Horizontal rule
      if (line.trim() === '---') {
        if (inList) { html += '</ul>'; inList = false; }
        if (inTable) { html += '</table>'; inTable = false; }
        html += '<hr>';
        continue;
      }

      // Headers
      if (line.startsWith('### ')) {
        if (inList) { html += '</ul>'; inList = false; }
        if (inTable) { html += '</table>'; inTable = false; }
        html += '<h4>' + inlineFormat(line.slice(4)) + '</h4>';
        continue;
      }

      // Table rows
      if (line.trim().startsWith('|')) {
        if (inList) { html += '</ul>'; inList = false; }
        // Skip separator rows
        if (/^\|\s*-/.test(line)) continue;
        var cells = line.split('|').filter(function (c) { return c.trim() !== ''; });
        if (!inTable) {
          html += '<table class="grammar-table"><tr>';
          cells.forEach(function (c) { html += '<th>' + inlineFormat(c.trim()) + '</th>'; });
          html += '</tr>';
          inTable = true;
        } else {
          html += '<tr>';
          cells.forEach(function (c) { html += '<td>' + inlineFormat(c.trim()) + '</td>'; });
          html += '</tr>';
        }
        continue;
      }
      if (inTable) { html += '</table>'; inTable = false; }

      // List items
      if (line.startsWith('- ')) {
        if (!inList) { html += '<ul>'; inList = true; }
        html += '<li>' + inlineFormat(line.slice(2)) + '</li>';
        continue;
      }
      if (inList) { html += '</ul>'; inList = false; }

      // Empty lines
      if (line.trim() === '') {
        continue;
      }

      // Regular paragraph
      html += '<p>' + inlineFormat(line) + '</p>';
    }
    if (inList) html += '</ul>';
    if (inTable) html += '</table>';
    return html;
  }

  function inlineFormat(text) {
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Code
    text = text.replace(/`(.+?)`/g, '<code>$1</code>');
    // Em dash
    text = text.replace(/ — /g, ' \u2014 ');
    return text;
  }

  // ============================================================
  // DARK MODE
  // ============================================================
  function loadDarkMode() {
    var saved = localStorage.getItem(DARK_KEY);
    if (saved === 'false') {
      document.body.classList.remove('dark');
    }
    // HTML defaults to dark; only remove if explicitly set to false
    updateDarkIcon();
  }

  function toggleDark() {
    document.body.classList.toggle('dark');
    localStorage.setItem(DARK_KEY, document.body.classList.contains('dark'));
    updateDarkIcon();
  }

  function updateDarkIcon() {
    var btn = document.getElementById('dark-toggle');
    if (btn) {
      btn.innerHTML = document.body.classList.contains('dark')
        ? '&#9790;'   // moon
        : '&#9788;';  // sun
    }
  }

  // ============================================================
  // INIT
  // ============================================================
  function init() {
    // Load settings
    settings = lsGet(SETTINGS_KEY) || JSON.parse(JSON.stringify(DEFAULT_SETTINGS));

    // Ensure all setting keys exist (forward-compat)
    Object.keys(DEFAULT_SETTINGS).forEach(function (k) {
      if (settings[k] === undefined) settings[k] = DEFAULT_SETTINGS[k];
    });

    loadDarkMode();

    // Load data
    fetch('data.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        DATA = data;
        console.log('SpanishKB Study loaded:',
          (data.words || []).length, 'words,',
          (data.conjugationPatterns || []).length, 'patterns,',
          (data.conjugationIrregulars || []).length, 'irregulars,',
          (data.medicalVocab || []).length, 'med vocab,',
          (data.medicalPhrases || []).length, 'med phrases');
        renderHome();
      })
      .catch(function (err) {
        console.error('Failed to load data.json:', err);
        document.getElementById('home-greeting').textContent = 'Error loading data';
        document.getElementById('home-streak').textContent =
          'Check that data.json exists in the app folder.';
      });
  }

  // ============================================================
  // PUBLIC API (used by HTML onclick handlers)
  // ============================================================
  window.SKB = {
    showView:         showView,
    startMode:        startMode,
    flipCard:         flipCard,
    rate:             rate,
    goHome:           goHome,
    toggleDark:       toggleDark,
    updateSetting:    updateSetting,
    toggleSetting:    toggleSetting,
    resetProgress:    resetProgress,
    exportProgress:   exportProgress,
    importProgress:   importProgress,
    handleImportFile: handleImportFile
  };

  // Boot
  init();
})();
