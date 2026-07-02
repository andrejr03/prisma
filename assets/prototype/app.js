/* ============================================================
   Prisma — Evaluation Command Center (design prototype)
   Static navigation + mock-data rendering. No dependencies.
   ============================================================ */
(function () {
  'use strict';

  var VIEWS = ['overview','evaluation','golden','regression','runtime','workflow','requests','context','citations'];

  /* -------- view switching + active menu highlight -------- */
  var navItems = Array.prototype.slice.call(document.querySelectorAll('.nav-item'));
  var side = document.getElementById('side');

  function showView(name) {
    if (VIEWS.indexOf(name) === -1) name = 'evaluation';
    VIEWS.forEach(function (v) {
      var el = document.getElementById('view-' + v);
      if (el) el.classList.toggle('active', v === name);
    });
    navItems.forEach(function (a) {
      a.classList.toggle('on', a.getAttribute('data-view') === name);
    });
    if (side) side.classList.remove('open');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (('#' + name) !== window.location.hash) {
      history.replaceState(null, '', '#' + name);
    }
  }

  /* -------- delegated navigation (menu, links, row jumps) -------- */
  document.addEventListener('click', function (e) {
    var nav = e.target.closest('[data-view]');
    if (nav) { e.preventDefault(); showView(nav.getAttribute('data-view')); return; }
    var goto = e.target.closest('[data-goto]');
    if (goto) { showView(goto.getAttribute('data-goto')); return; }
    var col = e.target.closest('[data-collapse]');
    if (col) {
      var panel = col.closest('.panel');
      if (panel) panel.classList.toggle('collapsed');
    }
  });

  /* -------- mobile sidebar toggle -------- */
  var hb = document.getElementById('hamburger');
  if (hb) hb.addEventListener('click', function () { side.classList.toggle('open'); });

  /* -------- request row selection -> detail panel -------- */
  document.addEventListener('click', function (e) {
    var row = e.target.closest('#req-body tr');
    if (!row) return;
    document.querySelectorAll('#req-body tr').forEach(function (r) { r.classList.remove('sel'); });
    row.classList.add('sel');
    var d = row.dataset;
    var idEl = document.getElementById('req-detail-id');
    var kv = document.getElementById('req-detail-kv');
    if (idEl) idEl.textContent = d.id;
    if (kv) {
      var statusColor = d.status === '200' ? 'var(--green)' : (d.status === 'retry' ? 'var(--amber)' : 'var(--red)');
      var statusText = d.status === '200' ? '200 OK' : (d.status === 'retry' ? 'retry' : d.status);
      kv.innerHTML =
        row_kv('route', '<b>' + d.route + '</b>') +
        row_kv('status', '<b style="color:' + statusColor + '">' + statusText + '</b>') +
        row_kv('latency', '<b>' + d.lat + '</b>') +
        row_kv('retrieved', '<b>' + d.retr + ' chunks</b>') +
        row_kv('tokens', '<b>' + d.tok + '</b>') +
        row_kv('provider', '<b>local:vllm/qwen2.5</b>') +
        row_kv('grounded', '<b style="color:' + (d.grounded === 'yes' ? 'var(--green)' : 'var(--amber)') + '">' + (d.grounded === 'yes' ? 'yes · 0 unsupported' : 'partial') + '</b>') +
        row_kv('cache', '<b>' + d.cache + '</b>');
    }
  });
  function row_kv(k, v) { return '<dt>' + k + '</dt><dd>' + v + '</dd>'; }

  /* ============ MOCK DATA ============ */

  // Requests (Request Inspector)
  var REQS = [
    { id:'req_9f3a1c', route:'rag.answer', retr:8,  tok:'1,204', lat:'438ms', status:'200',   grounded:'yes', cache:'miss' },
    { id:'req_9f3a1b', route:'agent.plan', retr:14, tok:'2,880', lat:'1.9s',  status:'200',   grounded:'yes', cache:'miss' },
    { id:'req_9f3a19', route:'rag.answer', retr:6,  tok:'902',   lat:'377ms', status:'200',   grounded:'yes', cache:'hit'  },
    { id:'req_9f3a18', route:'rag.rerank', retr:20, tok:'0',     lat:'120ms', status:'200',   grounded:'yes', cache:'hit'  },
    { id:'req_9f3a15', route:'agent.tool', retr:3,  tok:'640',   lat:'2.4s',  status:'retry', grounded:'partial', cache:'miss' },
    { id:'req_9f3a12', route:'rag.answer', retr:8,  tok:'1,110', lat:'455ms', status:'200',   grounded:'yes', cache:'miss' },
    { id:'req_9f3a0e', route:'rag.answer', retr:9,  tok:'1,332', lat:'521ms', status:'200',   grounded:'yes', cache:'hit'  },
    { id:'req_9f3a0a', route:'agent.plan', retr:0,  tok:'410',   lat:'1.1s',  status:'504',   grounded:'partial', cache:'miss' },
    { id:'req_9f3a07', route:'rag.answer', retr:7,  tok:'988',   lat:'399ms', status:'200',   grounded:'yes', cache:'hit'  },
    { id:'req_9f3a03', route:'index.query',retr:32, tok:'0',     lat:'84ms',  status:'200',   grounded:'yes', cache:'hit'  },
    { id:'req_9f39fe', route:'rag.answer', retr:8,  tok:'1,050', lat:'410ms', status:'200',   grounded:'yes', cache:'miss' },
    { id:'req_9f39fa', route:'agent.plan', retr:11, tok:'2,190', lat:'1.7s',  status:'200',   grounded:'yes', cache:'miss' }
  ];
  function reqStatusChip(s) {
    if (s === '200') return '<span class="chip ok">200</span>';
    if (s === 'retry') return '<span class="chip warnc">retry</span>';
    return '<span class="chip fail">' + s + '</span>';
  }
  var reqBody = document.getElementById('req-body');
  if (reqBody) {
    reqBody.innerHTML = REQS.map(function (r, i) {
      return '<tr class="' + (i === 0 ? 'sel' : '') + '"' +
        ' data-id="' + r.id + '" data-route="' + r.route + '" data-retr="' + r.retr +
        '" data-tok="' + r.tok + '" data-lat="' + r.lat + '" data-status="' + r.status +
        '" data-grounded="' + r.grounded + '" data-cache="' + r.cache + '">' +
        '<td class="idc">' + r.id + '</td><td>' + r.route + '</td>' +
        '<td class="num">' + r.retr + '</td><td class="num">' + r.tok + '</td>' +
        '<td class="num">' + r.lat + '</td><td>' + reqStatusChip(r.status) + '</td></tr>';
    }).join('');
  }

  // Golden cases (full table)
  var GOLDEN = [
    ['gc_multi_hop_014','multi-hop','faithfulness',0.98,0.90],
    ['gc_citation_071','citation','context-prec',0.81,0.72],
    ['gc_grounded_020','grounding','faithfulness',0.97,0.94],
    ['gc_agent_route_9','agent','exact-match',1.00,1.00],
    ['gc_refuse_008','refusal','exact-match',1.00,1.00],
    ['gc_rag_short_112','rag','relevance',0.88,0.93],
    ['gc_grounded_033','grounding','faithfulness',0.95,0.96],
    ['gc_longctx_155','long-context','context-prec',0.70,0.79],
    ['gc_agent_tool_41','agent','exact-match',0.96,0.96],
    ['gc_rag_long_204','rag','relevance',0.86,0.88],
    ['gc_citation_090','citation','context-prec',0.83,0.85],
    ['gc_multi_hop_051','multi-hop','faithfulness',0.92,0.93],
    ['gc_refuse_017','refusal','exact-match',1.00,1.00],
    ['gc_grounded_061','grounding','faithfulness',0.94,0.95]
  ];
  var goldenBody = document.getElementById('golden-body');
  if (goldenBody) {
    goldenBody.innerHTML = GOLDEN.map(function (g) {
      var base = g[3], now = g[4], d = +(now - base).toFixed(2);
      var fail = d < -0.02;
      var dCls = d < -0.001 ? 'down' : (d > 0.001 ? 'up' : 'flat');
      var dTxt = (d > 0 ? '+' : '') + d.toFixed(2);
      var nowColor = fail ? 'color:var(--red)' : (d > 0.001 ? 'color:var(--green)' : '');
      return '<tr data-goto="golden"><td class="idc">' + g[0] + '</td><td>' + g[1] + '</td><td>' + g[2] + '</td>' +
        '<td class="num">' + base.toFixed(2) + '</td>' +
        '<td class="num" style="' + nowColor + '">' + now.toFixed(2) + '</td>' +
        '<td class="num ' + dCls + '">' + dTxt + '</td>' +
        '<td>' + (fail ? '<span class="chip fail">fail</span>' : '<span class="chip ok">pass</span>') + '</td></tr>';
    }).join('');
  }

  /* ============ CHARTS (pure DOM bars) ============ */
  function renderBars(el, vals, opts) {
    if (!el) return;
    opts = opts || {};
    var min = opts.min, max = opts.max;
    if (min == null) min = Math.min.apply(null, vals) * 0.9;
    if (max == null) max = Math.max.apply(null, vals) * 1.05;
    el.innerHTML = vals.map(function (v) {
      var h = Math.max(3, Math.round(((v - min) / (max - min)) * 100));
      var col = opts.color || 'var(--blue)';
      if (opts.threshold != null) col = v < opts.threshold ? 'var(--red)' : 'var(--green)';
      var label = opts.fmt ? opts.fmt(v) : String(v);
      return '<i title="' + label + '" style="height:' + h + '%;background:linear-gradient(180deg,' + col + ',rgba(0,0,0,0))"></i>';
    }).join('');
  }

  // Evaluation baseline comparison — last value dips below gate
  renderBars(document.getElementById('eval-spark'),
    [0.985,0.982,0.979,0.984,0.981,0.977,0.983,0.980,0.978,0.975,0.968,0.940],
    { min:0.90, max:1.00, threshold:0.96, fmt:function(v){return v.toFixed(3);} });

  // Runtime latency p95 (ms)
  renderBars(document.getElementById('rt-lat'),
    [980,1020,1110,1240,1180,1090,1310,1420,1360,1290,1510,1310],
    { min:800, max:1600, color:'var(--amber)', fmt:function(v){return (v/1000).toFixed(2)+'s';} });

  // Runtime throughput (tok/s)
  renderBars(document.getElementById('rt-tok'),
    [72,68,74,81,88,79,76,84,91,86,78,78],
    { min:50, max:100, color:'var(--teal)', fmt:function(v){return v+' tok/s';} });

  /* ============ ROUTING (deep-link via hash) ============ */
  var initial = (window.location.hash || '').replace('#', '');
  showView(VIEWS.indexOf(initial) !== -1 ? initial : 'evaluation');
  window.addEventListener('hashchange', function () {
    var h = (window.location.hash || '').replace('#', '');
    if (VIEWS.indexOf(h) !== -1) showView(h);
  });
})();
