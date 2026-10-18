import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
f=GAME+'proto.html'; s=open(f).read()
def R(a,b,cnt=1):
    global s
    assert s.count(a)==cnt, (s.count(a), a[:140]); s=s.replace(a,b)

# ---------- tuning knobs of the prototype ----------
R("boostMul:1.32, riseK:1.3, landLead:1.1,", "boostMul:1.32, riseK:1.3, landLead:1.1, drainBase:0.02, drainCass:0.0035, pollFloor:10, multMax:5, voltZoneLen:5.0, voltWin:0.25, voltGest:100, ptsVolteZone:2, ptsWallHit:-2,")
R("ptsBronze:0.1, ptsSilver:0.2, ptsGold:0.4,", "ptsBronze:0.3, ptsSilver:0.6, ptsGold:1.2,")
R("ptsDodge:0.2, ptsHit:-0.1,", "ptsDodge:0.2, ptsHit:-1,")
R("ptsRam:0.2,", "ptsRam:0.4,")
s=s.replace("ptsHit: -0.05, wSmall: 5}", "ptsHit: -1, wSmall: 5}").replace("ptsHit: -0.1, wSmall: 5}", "ptsHit: -1, wSmall: 5}").replace("ptsHit: -0.15, wSmall: 6}", "ptsHit: -1, wSmall: 6}")
s=s.replace("cfGold: 30, ptsGold: 0.5,", "cfGold: 20, ptsGold: 1.2,").replace("cfGold: 20, ptsGold: 0.4,", "cfGold: 20, ptsGold: 1.2,")

# ---------- no tutorial, no adaptive difficulty: the core loop only ----------
R("ensureAudio(); tutoOn = tutoBox.checked; applyLevel(level); reset();", "ensureAudio(); tutoOn = false; applyLevel(level); reset();")
R("  setAdapt(tutoOn ? 1 : adaptSaved);", "  setAdapt(1);")

# ---------- polls are the life bar, casseroles make them drain ----------
R("""  if (weight >= 100 && !invincible){
    if (flags.sinkAt === undefined || flags.sinkAt === null) flags.sinkAt = gt + P.sinkDelay;
    else if (gt >= flags.sinkAt){ state = 'sinking'; endT = 0; endReason = 'sink'; sfx('sink'); if (!tutActive()) musicFade(); return; }
  } else flags.sinkAt = null;""",
"""  // the news cycle moves on: polls drain, faster with every casserole hanging on the board (game feel untouched)
  if (!invincible){
    poll = Math.max(0, poll - (P.drainBase + P.drainCass*weight)*gdt);
    if (poll <= P.pollFloor){ state = 'sinking'; endT = 0; endReason = 'polls'; sfx('sink'); musicFade(); return; }
  }""")
R("  weight = Math.min(100, weight + w); hudPop", "  weight = weight + w; breakMult(); hudPop")
R("  while (chain.items.length < target){", "  while (chain.items.length < Math.min(12, target)){")
R("endSink:'Coulée !',", "endPolls:'Décrochage !', endPollsText:'Les sondages sont tombés sous {f} %, le {d}.', endSink:'Coulée !',")
R("document.getElementById('endTitle').textContent = won ? TXT.endWin : reason === 'wall' ? TXT.endWall : TXT.endSink;",
  "document.getElementById('endTitle').textContent = won ? TXT.endWin : reason === 'polls' ? TXT.endPolls : reason === 'wall' ? TXT.endWall : TXT.endSink;")
R("document.getElementById('endText').textContent = won ? '' : (reason === 'wall' ? TXT.endWallText : TXT.endSinkText).replace('{d}', d);",
  "document.getElementById('endText').textContent = won ? '' : (reason === 'polls' ? TXT.endPollsText.replace('{f}', P.pollFloor) : reason === 'wall' ? TXT.endWallText : TXT.endSinkText).replace('{d}', d);")
# HUD: polls on a 0-40 scale with the floor marked, casseroles as a count
R("  bar(g1, (poll - 15)/20, COL_POLL, 'SONDAGES', fmtPct(poll), poll >= 30 ? '#86efac' : '#fff', 'poll');\n  ctx.fillStyle = 'rgba(20,33,61,.8)'; ctx.fillRect(gx + gw*0.75 - 1, g1 - 2, 2, gh + 4);",
  "  const danger = poll < P.pollFloor + 4, blink = danger && Math.sin(realT*10) > 0;\n  bar(g1, poll/40, blink ? '#ef4444' : COL_POLL, 'SONDAGES', fmtPct(poll), danger ? '#fecaca' : poll >= 30 ? '#86efac' : '#fff', 'poll');\n  ctx.fillStyle = '#ef4444'; ctx.fillRect(gx + gw*P.pollFloor/40 - 1, g1 - 3, 3, gh + 6);")
R("  bar(g2, weight/100, COL_CASS, 'CASSEROLES', Math.round(weight) + '/100', weight > 70 ? '#fecaca' : '#fff', 'cass');",
  "  bar(g2, weight/100, COL_CASS, 'CASSEROLES', String(Math.round(weight)), weight > 70 ? '#fecaca' : '#fff', 'cass');")

# ---------- multiplier: orbs and knocked-over journalists build it, a casserole or an interview breaks it ----------
R("function addPoll(v){ poll = Math.max(0, poll + v);", "let mult = 1, multT = -9, multBreakT = -9, multLost = 1;\nfunction bumpMult(){ if (mult < P.multMax){ mult++; multT = realT; sfx('up'); } }\nfunction breakMult(){ if (mult > 1){ multLost = mult; mult = 1; multBreakT = realT; sfx('miss'); } }\nfunction addPoll(v){ if (v > 0) v *= mult; poll = Math.max(0, poll + v);")
R("else if (inv <= 0){ o.hit = true; inv = 0.5; fallT = 0; stats.hit++;", "else if (inv <= 0){ o.hit = true; inv = 0.5; fallT = 0; stats.hit++; breakMult();")
R("addPoll(P.ptsRam * o.n, px + 10, py - 130);", "addPoll(P.ptsRam * o.n, px + 10, py - 130); bumpMult();")
R("    stats.actus++; orbCombo(); sparkle = true;", "    stats.actus++; orbCombo(); sparkle = true; setTimeout(bumpMult, 0);")
R("function drawGains(){", """function drawMult(){
  if (state !== 'play' || mode === 'volte') return;
  const p = w2s(PX() + 40, riderY() - 175), up = clamp((realT - multT)/0.25, 0, 1), br = realT - multBreakT;
  ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  if (br < 0.7){   // the multiplier shatters
    const k = br/0.7; ctx.globalAlpha = 1 - k; ctx.translate(p.x, p.y + 30*k); ctx.rotate(0.4*k); fontT(30, 900);
    ctx.lineWidth = 6; ctx.strokeStyle = '#1b2433'; ctx.strokeText('×' + multLost, 0, 0); ctx.fillStyle = '#ef4444'; ctx.fillText('×' + multLost, 0, 0);
  } else if (mult > 1){
    const sc = 1 + 0.6*Math.sin(up*Math.PI)*(1 - up*0.3) + 0.04*Math.sin(realT*8), col = ['#fff', '#fff', '#ffe066', '#ffb020', '#ff7a1a', '#ff3d6e'][mult];
    ctx.translate(p.x, p.y); ctx.scale(sc, sc); fontT(24 + mult*4, 900);
    ctx.lineWidth = 7; ctx.strokeStyle = '#1b2433'; ctx.strokeText('×' + mult, 0, 0); ctx.fillStyle = col; ctx.fillText('×' + mult, 0, 0);
  }
  ctx.restore();
}
function drawGains(){""")
R("  drawGains();\n", "  drawGains();\n  drawMult();\n  drawVolteHint();\n  drawThemeBanner();\n")

# ---------- gliding no longer knocks journalists over ----------
R("if ((charging && onWater) || gliding){ o.rammed = true;", "if (charging && onWater){ o.rammed = true;")

# ---------- gold orb: slow motion instead of a freeze, no choice; good timing = contre-feu ----------
R("  mode = 'grab'; targetScale = 0.04; charging = false; holding = false;", "  mode = 'grab'; targetScale = 0.3; charging = false; holding = false;")
R("else if (mode === 'grab' && state === 'play'){ tz = P.grabZoom; tx = PX() + 40; ty = riderY() - 60; }",
  "else if (mode === 'grab' && state === 'play'){ tz = P.camZoom*1.35; tx = PX() + 120; ty = riderY() - 40; }")
R("  grabEnd(Math.abs(p - P.grabTarget) <= grab.win/2 ? 'ok' : (p < P.grabTarget ? 'early' : 'late'));",
  "  grab.perfect = Math.abs(p - P.grabTarget) <= grab.win/5;\n  grabEnd(Math.abs(p - P.grabTarget) <= grab.win/2 ? 'ok' : (p < P.grabTarget ? 'early' : 'late'));")
R("""  if (res !== 'ok'){ pop(res === 'early' ? TXT.grabEarly : TXT.grabLate, C.red, PX() + 30, riderY() - 160, true); sfx('miss'); return; }
  stats.actus++; sfx('catch'); sparkle = true; if (tutActive()) tutS.caught = (tutS.caught || 0) + 1;
  pop(TXT.grabOk, C.blue, PX() + 30, riderY() - 170);
  const d = pickActu();
  pending = Object.assign({tier: grab.tier}, d);
  if (grab.tier !== 'g'){ pending.choice = 'rec'; applyActu(); }""",
"""  // the gold orb always brings polls; good timing also lights a contre-feu (perfect: every casserole goes)
  stats.actus++; sfx('catch'); sparkle = true;
  pending = Object.assign({tier: grab.tier, choice: 'rec'}, pickActu()); applyActu(); bumpMult();
  if (res !== 'ok'){ pop(TXT.grabMissed, C.muted, PX() + 30, riderY() - 160, true); return; }
  const n = grab.perfect ? Math.ceil(weight) : P.cfGold;
  if (n > 0){ detach(n); stats.cf++; hudPop('cass', '−' + n + ' cass.', true, -n); sfx('fire'); }
  pop(grab.perfect ? TXT.cfPerfect : TXT.cfGood, grab.perfect ? '#16a34a' : C.blue, PX() + 30, riderY() - 175, true);""")
R("    const ok = grab.res === 'ok' && pending && !pending.done;\n    grab = null;\n    if (ok){ mode = 'choice'; targetScale = 0; choice = {t: 0, tut: tutActive() && !flags.choiceTut ? 1 : 0}; if (choice.tut) flags.choiceTut = true; }\n    else { mode = null; targetScale = 1; }",
  "    grab = null; mode = null; targetScale = 1;")
R("if (grab.rt >= (grab.res === 'ok' ? 1.05 : 0.6)){", "if (grab.rt >= 0.5){")
R("if (grab){ const ok = grab.res === 'ok', hf", "if (grab){ const ok = !!grab.res, hf")
R("  if (grab) return grab.res === 'ok' ?", "  if (grab) return grab.res ?")
R("waitTap:'Appuie", "grabMissed:'Actu récupérée', cfGood:'Contre-feu ! −' + 20 + ' casseroles', cfPerfect:'Contre-feu parfait ! Plus une casserole', waitTap:'Appuie")

# ---------- volte-face: a gesture at the apex of a charged jump ----------
R("let ramAt = -9,", "let jumpCharge = 0, apexGT = -9, voltGes = null, voltOkT = -9, voltOkFree = false, theme = null, themeT = -9, ramAt = -9,")
s = s.replace("{ const v = P.jumpMin + (P.jumpMax-P.jumpMin)*charge; vy = -v/P.riseK;", "{ jumpCharge = charge; const v = P.jumpMin + (P.jumpMax-P.jumpMin)*charge; vy = -v/P.riseK;")
assert "jumpCharge = charge;" in s
R("    vy += (vy < 0 ? P.gravity/(P.riseK*P.riseK) : P.gravity) * gdt;\n",
  "    { const vy0 = vy; vy += (vy < 0 ? P.gravity/(P.riseK*P.riseK) : P.gravity) * gdt; if (vy0 < 0 && vy >= 0) apexGT = gt; }\n")
R("function pointerUp(){ ptrDown = false;", "function pointerUp(){ ptrDown = false; voltGes = null;")
R("cv.addEventListener('pointerdown', e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch(_){} pointerDown(toLocal(e)); });",
  "cv.addEventListener('pointerdown', e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch(_){} const p = toLocal(e); pointerDown(p); voltStart(p); });\ncv.addEventListener('pointermove', e => { if (voltGes) voltMove(toLocal(e)); });")
R("window.addEventListener('keydown', e => {\n  if (e.target && e.target.tagName === 'INPUT') return;",
  "window.addEventListener('keydown', e => {\n  if (e.target && e.target.tagName === 'INPUT') return;\n  if ((e.code === 'KeyV' || e.code === 'ArrowLeft') && state === 'play' && !mode && !paused){ e.preventDefault(); if (voltWindow()) doVolte(); return; }")
R("function press(){", r"""// the window: a quarter of a second each side of the apex of a charged jump
function voltWindow(){
  if (onWater || jumpCharge < 0.8 || state !== 'play' || mode) return false;
  const gu = P.gravity/(P.riseK*P.riseK);
  return vy < 0 ? -vy/gu <= P.voltWin : gt - apexGT <= P.voltWin;
}
function voltStart(p){ voltGes = (state === 'play' && !mode && voltWindow()) ? {t0: realT, last: p, len: 0, turn: 0, h: null} : null; }
function voltMove(p){
  const g = voltGes; if (!g) return;
  if (realT - g.t0 > 0.6 || onWater){ voltGes = null; return; }
  const dx = p.x - g.last.x, dy = p.y - g.last.y, d = Math.hypot(dx, dy); if (d < 5) return;
  const h = Math.atan2(dy, dx);
  if (g.h !== null){ let dh = h - g.h; while (dh > Math.PI) dh -= 2*Math.PI; while (dh < -Math.PI) dh += 2*Math.PI; g.turn += dh; }
  g.h = h; g.len += d; g.last = p;
  // from the bottom, round by the right, up and to the left: the heading turns anticlockwise on screen
  if (-g.turn*180/Math.PI >= P.voltGest && g.len >= 50){ voltGes = null; doVolte(); }
}
function doVolte(){
  holding = false; turnT = 0; sfx('whoosh'); sfx('tack');
  sea = sea === 'large' ? 'cote' : 'large';
  const z = obs.find(o => o.kind === 'wall' && !o.done && t >= o.w - P.voltZoneLen && t < o.w + 0.2);
  voltOkT = realT; voltOkFree = !z;
  if (!z) return;   // a free about-turn: for the fun of it, and to practise
  z.done = true; z.opened = realT; stats.good++;
  for (const o of obs) if (o.kind === 'sand' && Math.abs(o.w - z.w) < 0.5) o.turned = true;
  const d = voltData(z.idx); theme = {old: d.oldS, neu: d.neuS, sujet: d.sujet}; themeT = realT;
  addPoll(P.ptsVolteZone, PX() + 30, riderY() - 150); bumpMult();
}
const VSHORT = [['Entente avec Poutine', 'Stop aux opérations russes'], ['Quitter l’OTAN intégrée', 'Rester dans l’OTAN intégrée'], ['Interdire le voile', 'Le Parlement décidera'], ['Le Parlement décidera', 'Référendum sur le voile'], ['Rejeter la loi immigration', 'Voter la loi immigration'], ['Abroger ? Nous verrons', 'Abroger à l’automne'], ['Âge légal intouchable', 'Âge légal à l’étude'], ['Zéro TVA sur 100 produits', 'Seulement si forte inflation'], ['Seulement si forte inflation', 'Zéro TVA au contre-budget'], ['Sortir du marché européen', 'Négocier une dérogation'], ['Inéligibilité à vie', '« Une décision politique »'], ['Contre la sûreté nucléaire', 'Pour la même réforme']];
function voltData(idx){ const k = voltOrder.length ? voltOrder[idx % voltOrder.length] : idx % VOLTES.length, d = VOLTES[k], sh = VSHORT[k] || [d.old, d.neu]; return Object.assign({oldS: sh[0], neuS: sh[1]}, d); }
function drawVolteHint(){
  // a half-circle arrow under Marine during the window, filling as the gesture is traced
  const ok = realT - voltOkT;
  if (!(voltWindow() || ok < 0.5)) return;
  const p = w2s(PX() + 6, riderY() + 46), r = 34, g = voltGes, k = ok < 0.5 ? 1 : g ? clamp(-g.turn*180/Math.PI/P.voltGest, 0, 1) : 0, pulse = 0.5 + 0.5*Math.sin(realT*18);
  ctx.save(); ctx.lineCap = 'round'; ctx.globalAlpha = ok < 0.5 ? 1 - ok*2 : 1;
  ctx.lineWidth = 9; ctx.strokeStyle = 'rgba(15,29,51,.75)'; ctx.beginPath(); ctx.arc(p.x, p.y, r, Math.PI/2, -Math.PI/2, true); ctx.stroke();
  ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(255,255,255,' + (0.55 + 0.4*pulse) + ')'; ctx.beginPath(); ctx.arc(p.x, p.y, r, Math.PI/2, -Math.PI/2, true); ctx.stroke();
  if (k > 0){ ctx.strokeStyle = ok < 0.5 ? '#2fb24e' : '#ffd23f'; ctx.beginPath(); ctx.arc(p.x, p.y, r, Math.PI/2, Math.PI/2 - k*Math.PI, true); ctx.stroke(); }
  const ay = p.y - r; ctx.fillStyle = ok < 0.5 ? '#2fb24e' : '#fff'; ctx.strokeStyle = 'rgba(15,29,51,.85)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(p.x - 14, ay); ctx.lineTo(p.x, ay - 10); ctx.lineTo(p.x, ay + 10); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
}
function drawThemeBanner(){
  // after a volte-face in a zone: the new official position, for a few seconds
  if (!theme || realT - themeT > 3.6 || mode) return;
  const k = realT - themeT, a = clamp(k*5, 0, 1)*clamp((3.6 - k)*3, 0, 1);
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  font(15, 800); const w1 = ctx.measureText(theme.neu).width; fontT(22, 900); const w = Math.max(w1, ctx.measureText(theme.neu).width) + 60, x = VW/2 - w/2, y = 128;
  panel(x, y, w, 70, PAPER, 10); font(11, 900); ctx.fillStyle = C.green; ctx.fillText('NOUVELLE POSITION · ' + theme.sujet.toUpperCase(), VW/2, y + 24, w - 30);
  fontT(22, 900); ctx.fillStyle = C.ink; ctx.fillText(theme.neu, VW/2, y + 54, w - 30);
  font(11, 800); ctx.fillStyle = C.red; ctx.fillText('avant : ' + theme.old, VW/2, y + 86, w);
  ctx.restore();
}
function press(){""")
# zones: longer and free of obstacles; the first one is explained once
R("function voltZone(v, warned){ return {a: v - (warned ? P.approachLead + 0.4 : 1.7), b: v + P.voltAfter}; }",
  "function voltZone(v, warned){ return {a: v - P.voltZoneLen - 0.4, b: v + P.voltAfter}; }")
R("else { const v = cur + (it.first ? P.approachLead + 0.4 : 1.7),", "else { const v = cur + P.voltZoneLen + 0.4,")
R("if (live && onWater && o.kind === 'wall' && !o.warned && x - px < P.approachLead*pxw){", "if (live && onWater && o.kind === 'wall' && !o.warned && x - px < (P.voltZoneLen + 0.3)*pxw){")
R("approach:{kicker:'VOLTE-FACE', title:'On va se prendre un mur !', text:'Il est temps de changer d’avis.', bl:'Je retourne ma veste'}",
  "approach:{kicker:'ZONE DE VOLTE-FACE', title:'Change de bord avant le mur !', text:'Fais un saut chargé. À son sommet, trace un demi-tour : du bas, par la droite, vers le haut à gauche.', bl:'Je retourne ma veste'}")
# the wall: no jumping over it any more; done = it sinks; missed = crash, penalty, the position flips anyway
R("""    } else if (o.kind === 'wall' && !o.done && live){
      if (!o.hit && Math.abs(x - px) < o.wid/2 + 16 && py > WATER - 91*WALL_S + 6){
        o.hit = true;
        if (!invincible){ o.done = true; stats.fail++; if (tutActive()) tutS.fail = true; startVolte(o.idx); vf.phase = 'impact'; vf.t = 0; vf.chips = [chipCass(P.wWall)]; attach(P.wWall, false, null); sfx('wall'); return; }
      }
      if (x <= px - 10){ o.done = true; startVolte(o.idx); return; }
    }""",
"""    } else if (o.kind === 'wall' && !o.done && live){
      if (!o.hit && Math.abs(x - px) < o.wid/2 + 16){
        o.hit = true; o.done = true;
        if (!invincible){ stats.fail++; startVolte(o.idx); vf.phase = 'impact'; vf.t = 0; vf.chips = [chipCass(P.wWall), chipPoll(P.ptsWallHit)]; attach(P.wWall, false, null); addPoll(P.ptsWallHit); sfx('wall');
          const d = voltData(o.idx); theme = {old: d.oldS, neu: d.neuS, sujet: d.sujet}; themeT = realT + 1e3; vf.forcedTheme = true; return; }
      }
    }""")
R("function volteDone(){", "function volteDone(){\n  if (vf && vf.forcedTheme) themeT = realT;")
# zone decor: buoys and pennants along the zone, the theme sign above; the wall sinks once the turn is made
R("      else if (o.kind === 'wall') spr(o.hit ? 'wallCr' : 'wall', x, WATER + 2, WALL_S);",
  """      else if (o.kind === 'wall'){
        drawVoltZone(o);
        const sink = o.opened ? clamp((realT - o.opened)/0.7, 0, 1) : 0;
        if (sink < 1){ ctx.save(); ctx.globalAlpha = 1 - sink*0.6; spr(o.hit ? 'wallCr' : 'wall', x, WATER + 2 + sink*120, WALL_S); ctx.restore(); } }""")
R("function drawSand(o){", r"""function drawVoltZone(o){
  const pxw = P.pxPerWeek, x1 = sx(o.w), x0 = sx(o.w - P.voltZoneLen), d = voltData(o.idx);
  for (let w = o.w - P.voltZoneLen; w < o.w - 0.3; w += 0.42){
    const x = sx(w), bob = Math.sin(realT*3 + w*5)*2, red = Math.round(w/0.42) % 2;
    ctx.fillStyle = red ? '#e4572e' : '#fff'; ctx.beginPath(); ctx.moveTo(x - 7, WATER + 4 + bob); ctx.lineTo(x + 7, WATER + 4 + bob); ctx.lineTo(x, WATER - 14 + bob); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#1b2433'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = '#5a6988'; ctx.fillRect(x - 1, WATER - 40 + bob, 2, 28);
    ctx.fillStyle = o.done ? '#2fb24e' : (red ? '#ffd23f' : '#e4572e'); ctx.beginPath(); ctx.moveTo(x + 1, WATER - 40 + bob); ctx.lineTo(x + 15 + Math.sin(realT*6 + w)*2, WATER - 35 + bob); ctx.lineTo(x + 1, WATER - 30 + bob); ctx.closePath(); ctx.fill();
  }
  // the theme, floating above the zone
  const cx = (x0 + x1)/2, txt = o.done ? d.neuS : d.oldS;
  ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; fontT(30, 900); const w = ctx.measureText(txt).width + 70, y = WATER - 230;
  panel(cx - w/2, y, w, 82, o.done ? '#e9f8ee' : PAPER, 12);
  font(13, 900); ctx.fillStyle = o.done ? C.green : C.red; ctx.fillText((o.done ? 'NOUVELLE POSITION · ' : 'VOLTE-FACE · ') + d.sujet.toUpperCase(), cx, y + 28, w - 30);
  fontT(30, 900); ctx.fillStyle = C.ink; ctx.fillText(txt, cx, y + 66, w - 30);
  ctx.restore();
}
function drawSand(o){""")
R("get mode(){ return mode; },", "get mode(){ return mode; }, get mult(){ return mult; }, get poll(){ return poll; }, voltWindow, doVolte, get jumpCharge(){ return jumpCharge; },")
open(f,'w').write(s); print('ok')
