import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
import re
f=GAME+'proto.html'; s=open(f).read()
def R(a,b,cnt=1):
    global s
    assert s.count(a)==cnt, (s.count(a), a[:160]); s=s.replace(a,b)
def cut(a_start, b_start, new):
    global s
    i=s.index(a_start); j=s.index(b_start, i); s=s[:i]+new+s[j:]

# ---------- knobs ----------
R("voltZoneLen:7.0, voltWin:0.25, voltGest:100, ptsVolteZone:2,", "voltZoneLen:7.0, swipeDist:40, swipeTime:0.35, turnWeeks:1.4, turnSlow:0.6, ptsVolteMin:1, ptsVolteMax:5, tierTime:0.8, tierMul:[1.32, 1.55, 1.8], fastShare:0.25, grabSlow:0.04,")
# shorter flights: 30 % less air time and height on the full charged jump; the smallest hop keeps its height
R("gravity:900, jumpMin:330, jumpMax:560, chargeTime:0.45, glideTime:1.4,", "gravity:1286, jumpMin:394, jumpMax:560, chargeTime:0.45, glideTime:0.98,")

# ---------- swipe left = volte-face, in every state but the glide ----------
cut("// the window: a quarter of a second each side", "function doVolte(){", r"""// a swipe to the left turns Marine round, whatever she is doing, unless she is already gliding
let swipe = null, turn = null, speedTier = 0, fullT = 0;
const gliding = () => !onWater && holding && glideLeft > 0 && vy > 0;
function swipeStart(p){ swipe = (state === 'play' && !mode && !paused) ? {x: p.x, y: p.y, t0: realT, glide: gliding()} : null; }
function swipeMove(p){
  const g = swipe; if (!g) return;
  if (realT - g.t0 > P.swipeTime){ swipe = null; return; }
  const dx = p.x - g.x, dy = p.y - g.y;
  if (dx <= -P.swipeDist && Math.abs(dy) < -dx*0.9){ swipe = null; if (!g.glide) doVolte(); }
}
""")
cut("function doVolte(){", "const VSHORT = [", r"""function doVolte(){
  if (state !== 'play' || mode || gliding()) return;
  // the swipe began with a press: drop the charge or the glide that press started, without jumping
  charging = false; charge = 0; holding = false;
  const z = obs.find(o => o.kind === 'wall' && !o.done && t >= o.w - P.voltZoneLen && t < o.w + 0.2);
  turn = {t: 0, zone: z || null, close: z ? clamp(1 - (z.w - t)/P.voltZoneLen, 0, 1) : 0, flipped: false};
  mode = 'turn'; targetScale = 0.12; turnT = 0; sfx('whoosh');
}
const TURN_IN = 0.2, TURN_PANEL = 0.17, TURN_OUT = 0.25, TURN_END = TURN_IN + 3*TURN_PANEL + TURN_OUT;
function updateTurn(dt){
  const T = turn; T.t += dt;
  if (T.t >= TURN_IN && !T.snd){ T.snd = true; sfx('tack'); }
  if (!T.flipped && T.t >= TURN_IN + 1.5*TURN_PANEL){ T.flipped = true; flipWorld(); }
  if (T.t >= TURN_END){ mode = null; targetScale = 1; turn = null; }
}
function flipWorld(){
  // what was in front of Marine is now behind her; the calendar kept running while she turned
  const T = turn, t0 = t, t1 = t + P.turnWeeks, view = (VW/(P.camZoom*0.9))/P.pxPerWeek + P.turnWeeks;
  const mir = w => t1 - (w - t0) - 0.05;
  for (const o of obs){ if (o.kind === 'wall' || o.kind === 'sand') continue; if (o.w > t0 && o.w <= t0 + view){ o.w = mir(o.w); if (o.kind === 'boat' || o.kind === 'cass') o.passed = true; } }
  for (const a of actus){ if (!a.got && a.w > t0 && a.w <= t0 + view){ a.w = mir(a.w); a.gone = true; } }
  t = t1; nextObs = Math.max(nextObs, t + 0.6);
  sea = sea === 'large' ? 'cote' : 'large';
  // the turn costs the speed: Marine sets off again slowly
  speedTier = 0; fullT = 0; spdMul = P.turnSlow; if (!onWater) jumpSpd = Math.min(jumpSpd, P.turnSlow + 0.2);
  const z = T.zone;
  if (!z) return;   // a free about-turn: for the fun of it, and to practise
  z.done = true; z.opened = realT; stats.good++;
  for (const o of obs) if (o.kind === 'sand' && Math.abs(o.w - z.w) < 0.5) o.turned = true;
  // the later the turn, the bigger the reward
  const pts = P.ptsVolteMin + (P.ptsVolteMax - P.ptsVolteMin)*T.close*T.close;
  addPoll(pts, PX() + 30, riderY() - 150); bumpMult();
  T.label = T.close > 0.85 ? 'In extremis !' : T.close > 0.5 ? 'Pile à temps !' : 'Volte-face !';
  pop(T.label, T.close > 0.85 ? '#16a34a' : C.blue, PX() + 30, riderY() - 185, true);
}
function drawTurn(){
  if (mode !== 'turn' || !turn) return;
  const k = turn.t - TURN_IN;
  if (k < 0 || k >= 3*TURN_PANEL || !(tackImg.complete && tackImg.naturalWidth)) return;
  // the three panels of the tack, cut in one after the other
  const i = Math.min(2, Math.floor(k/TURN_PANEL)), e = (k - i*TURN_PANEL)/TURN_PANEL;
  const fw = tackImg.naturalWidth/3, fh = tackImg.naturalHeight, ph = H*0.86, pw = ph*fw/fh, sc = 1.04 - 0.04*e;
  const cx = VW/2 + (i - 1)*pw*0.18, cy = H/2;
  ctx.save(); ctx.fillStyle = 'rgba(10,18,32,' + (0.55 + 0.1*i) + ')'; ctx.fillRect(0, 0, VW, H);
  ctx.translate(cx, cy); ctx.rotate((i - 1)*0.035); ctx.scale(sc, sc); ctx.imageSmoothingEnabled = true;
  ctx.fillStyle = '#fff'; ctx.fillRect(-pw/2 - 6, -ph/2 - 6, pw + 12, ph + 12);
  ctx.drawImage(tackImg, i*fw, 0, fw, fh, -pw/2, -ph/2, pw, ph);
  if (e < 0.25){ ctx.globalAlpha = 1 - e/0.25; ctx.fillStyle = '#fff'; ctx.fillRect(-pw/2, -ph/2, pw, ph); }
  ctx.restore();
}
""")
cut("function drawVolteHint(){", "function drawThemeBanner(){", r"""function drawVolteHint(){
  // inside a zone: a left arrow under Marine, pulsing faster as the wall gets closer
  if (state !== 'play' || mode) return;
  const z = obs.find(o => o.kind === 'wall' && !o.done && t >= o.w - P.voltZoneLen && t < o.w);
  if (!z) return;
  const c = clamp(1 - (z.w - t)/P.voltZoneLen, 0, 1), pulse = 0.5 + 0.5*Math.sin(realT*(6 + 14*c)), p = w2s(PX() - 4, WATER + 52);
  ctx.save(); ctx.translate(p.x - pulse*8, p.y); ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-34, 0); ctx.lineTo(-10, -18); ctx.lineTo(-10, -8); ctx.lineTo(30, -8); ctx.lineTo(30, 8); ctx.lineTo(-10, 8); ctx.lineTo(-10, 18); ctx.closePath();
  ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(15,29,51,.85)'; ctx.stroke(); ctx.fillStyle = c > 0.85 ? '#2fb24e' : c > 0.5 ? '#ffd23f' : '#fff'; ctx.fill();
  ctx.restore();
}
""")
R("cv.addEventListener('pointerdown', e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch(_){} const p = toLocal(e); pointerDown(p); voltStart(p); });\ncv.addEventListener('pointermove', e => { if (voltGes) voltMove(toLocal(e)); });",
  "cv.addEventListener('pointerdown', e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch(_){} const p = toLocal(e); swipeStart(p); pointerDown(p); });\ncv.addEventListener('pointermove', e => { if (swipe) swipeMove(toLocal(e)); });")
R("function pointerUp(){ ptrDown = false; voltGes = null;", "function pointerUp(){ ptrDown = false; swipe = null;")
R("if ((e.code === 'KeyV' || e.code === 'ArrowLeft') && state === 'play' && !mode && !paused){ e.preventDefault(); if (voltWindow()) doVolte(); return; }",
  "if ((e.code === 'KeyV' || e.code === 'ArrowLeft') && state === 'play' && !mode && !paused){ e.preventDefault(); if (!e.repeat) doVolte(); return; }")
R("    else if (mode === 'grab') updateGrab(rdt);\n", "    else if (mode === 'grab') updateGrab(rdt);\n    else if (mode === 'turn') updateTurn(rdt);\n")
R("  else if (mode === 'grab' && state === 'play'){ tz = P.camZoom*1.35; tx = PX() + 120; ty = riderY() - 40; }",
  "  else if (mode === 'grab' && state === 'play'){ tz = P.camZoom*2.7; tx = PX() + 70; ty = riderY() - 85; }\n  else if (mode === 'turn' && state === 'play'){ const out = turn && turn.t > TURN_END - TURN_OUT; tz = out ? P.camZoom : P.camZoom*2.6; tx = PX() + (out ? (VW/2 - PX())/P.camZoom : 10); ty = out ? WATER + 40 + (H/2 - WATER - 40)/P.camZoom : riderY() - 75; }")
R("  const k = Math.min(1, rdt*(mode === 'grab' ? 8 : 4));", "  const k = Math.min(1, rdt*(mode === 'grab' ? 8 : mode === 'turn' ? 14 : 4));")
R("  drawGrabClose();\n  drawGrabGauge();", "  drawTurn();\n  drawGrabClose();\n  drawGrabGauge();")
R("if (!((mode === 'card' && card && !card.mini && !card.wait) || mode === 'cine' || mode === 'volte' ||", "if (!((mode === 'card' && card && !card.mini && !card.wait) || mode === 'cine' || mode === 'volte' || mode === 'turn' ||")
R("approach:{kicker:'ZONE DE VOLTE-FACE', title:'Change de bord avant le mur !', text:'Fais un saut chargé. À son sommet, trace un demi-tour : du bas, par la droite, vers le haut à gauche.',",
  "approach:{kicker:'ZONE DE VOLTE-FACE', title:'Change de bord avant le mur !', text:'Glisse vers la gauche pour faire volte-face. Plus tu attends le mur, plus ça rapporte.',")

# ---------- speed builds while the charge is held ----------
R("  if (charging && onWater) spdMul = 1 + (P.boostMul - 1)*charge;\n  else if (!onWater) spdMul = jumpSpd;\n  else spdMul += (1 - spdMul)*Math.min(1, gdt*3);",
  """  if (charging && onWater){
    if (charge >= 1){ fullT += gdt; const k = Math.min(P.tierMul.length - 1, Math.floor(fullT/P.tierTime)); if (k > speedTier){ speedTier = k; sfx('full'); camKick = 0.5; } }
    const target = charge < 1 ? 1 + (P.boostMul - 1)*charge : P.tierMul[speedTier];
    spdMul += (target - spdMul)*Math.min(1, gdt*(spdMul < target ? 2.5 : 8));
  }
  else if (!onWater) spdMul = jumpSpd;
  else { speedTier = 0; fullT = 0; spdMul += (1 - spdMul)*Math.min(1, gdt*(spdMul < 1 ? 1.2 : 3)); }""")
R("jumpSpd = jFac(v); spdMul = jumpSpd; }", "jumpSpd = charge >= 1 ? Math.max(jFac(v), spdMul) : jFac(v); spdMul = jumpSpd; }")
R("if (keepHold){ charging = true; charge = clamp((jumpSpd - 1)/(P.boostMul - 1), 0, 1); spdMul = 1 + (P.boostMul - 1)*charge; sfx('charge'); }",
  "if (keepHold){ charging = true; charge = clamp((jumpSpd - 1)/(P.boostMul - 1), 0, 1); spdMul = jumpSpd; sfx('charge'); }")
R("function drawChargeBar(px){\n  const w = 64, h = 7, x = px - w/2 - 6, y = WATER + 14, full = charge >= 1;",
  "function drawChargeBar(px){\n  const w = 64, h = 7, x = px - w/2 - 6, y = WATER + 14, full = charge >= 1;\n  if (full && speedTier > 0){ ctx.save(); font(13, 900); ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.lineWidth = 4; ctx.strokeStyle = '#1b2433'; const s = '›'.repeat(speedTier + 1); ctx.strokeText(s, x + w + 8, y + 4); ctx.fillStyle = speedTier > 1 ? '#ff7a1a' : '#ffe066'; ctx.fillText(s, x + w + 8, y + 4); ctx.restore(); }")

# ---------- speed orbs: ghosts that only solidify at high speed, and pay double ----------
R("function makeOrbObj(w, tier, h, diff, trap){ return {w, h, tier, trap: !!trap, diff, ph: rnd(0, 6.28), kind: ri(0, 2), got: false}; }",
  "function makeOrbObj(w, tier, h, diff, trap){ return {w, h, tier, trap: !!trap, diff, ph: rnd(0, 6.28), kind: ri(0, 2), got: false, fast: tier !== 'g' && ((Math.floor(w*137 + h*7) % 100) < 100*P.fastShare)}; }\nconst fastOk = () => spdMul >= P.tierMul[1] - 0.02;")
R("    if (!live) continue;\n    const R = P.touchR", "    if (!live || a.gone || (a.fast && !fastOk())) continue;\n    const R = P.touchR")
R("    pending = Object.assign({tier: a.tier, choice: 'rec'}, pickActu()); if (a.tier === 's') sfx('cash'); applyActu();\n    return;",
  "    pending = Object.assign({tier: a.tier, choice: 'rec'}, pickActu()); if (a.tier === 's') sfx('cash'); applyActu();\n    if (a.fast){ addPoll(a.tier === 's' ? P.ptsSilver : P.ptsBronze, PX() + 30, riderY() - 160); pop('Vitesse !', '#ff7a1a', PX() + 20, riderY() - 190); }\n    return;")
R("    for (const a of actus){ if (a.got || a.x === undefined) continue; orbSpr(a.tier, Math.floor(realT*(a.tier === 'g' ? 16 : 10) + a.ph) % 4, a.x, a.y, 1); }",
  """    for (const a of actus){ if (a.got || a.x === undefined) continue;
      const ghost = a.fast && !fastOk();
      if (a.fast){ ctx.save(); ctx.globalAlpha = ghost ? 0.5 : 0.9; ctx.strokeStyle = ghost ? '#cfe8ff' : '#ff7a1a'; ctx.lineWidth = 3; for (let i=0;i<3;i++){ const yy = a.y - 10 + i*10, l = 18 + 10*Math.sin(realT*12 + i); ctx.beginPath(); ctx.moveTo(a.x - 22 - l, yy); ctx.lineTo(a.x - 22, yy); ctx.stroke(); } ctx.restore(); }
      if (ghost){ ctx.save(); ctx.globalAlpha = 0.35 + 0.1*Math.sin(realT*8 + a.ph); }
      orbSpr(a.tier, Math.floor(realT*(a.tier === 'g' ? 16 : 10) + a.ph) % 4, a.x, a.y, 1);
      if (ghost) ctx.restore(); }""")

# ---------- gold orb: dramatic zoom on Marine reaching out, ultra slow motion, the gauge decides ----------
R("  mode = 'grab'; targetScale = 0.3; charging = false; holding = false;", "  mode = 'grab'; targetScale = P.grabSlow; charging = false; holding = false;")
cut("function drawGrabClose(){", "function drawGrabGauge(){", r"""function drawGrabClose(){
  // no cut-away any more: the camera dives on Marine, the world almost stops, the orb drifts to her hand
  if (mode !== 'grab' || !grab) return;
  const p = clamp(grab.t/grab.dur, 0, 1), ok = grab.res === 'ok';
  ctx.save(); const vg = ctx.createRadialGradient(VW/2, H/2, H*0.3, VW/2, H/2, H*0.95); vg.addColorStop(0, 'rgba(10,18,32,0)'); vg.addColorStop(1, 'rgba(10,18,32,.55)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, VW, H); ctx.restore();
  const hand = w2s(PX() + 52, riderY() - 128), st = w2s(PX() + 330, riderY() - 260);
  let ox, oy;
  if (ok){ ox = hand.x; oy = hand.y; }
  else if (grab.res){ ox = hand.x + grab.rt*420; oy = hand.y - grab.rt*300; }
  else { const k = clamp(p/P.grabTarget, 0, 1.25), e = 1 - Math.pow(1 - Math.min(k, 1), 2); ox = lerp(st.x, hand.x, e) + (k > 1 ? (k - 1)*160 : 0); oy = lerp(st.y, hand.y, e) + Math.sin(realT*14)*3; }
  orbGlow(ox, oy, 40); orbSpr(grab.tier, Math.floor(realT*14) % 4, ox, oy, 0.95);
  if (ok){ const a = clamp(grab.rt/0.25, 0, 1), sc = 0.6 + 0.5*Math.sin(a*Math.PI/2) - 0.1*a;
    ctx.save(); ctx.translate(ox + 40, oy - 60); ctx.rotate(-0.12);
    ctx.globalAlpha = 0.5; ctx.fillStyle = '#ffe066'; for (let i=0;i<12;i++){ ctx.save(); ctx.rotate(i*Math.PI/6 + realT*0.8); ctx.fillRect(0, -6, 120*sc, 12); ctx.restore(); }
    ctx.globalAlpha = 1; ctx.scale(sc*1.4, sc*1.4); font(30, 900); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineWidth = 7; ctx.strokeStyle = '#1b2433'; ctx.strokeText(TXT.caught, 0, 0); ctx.fillStyle = '#ffd23f'; ctx.fillText(TXT.caught, 0, 0); ctx.restore();
    ctx.textBaseline = 'alphabetic';
    ctx.save(); ctx.globalAlpha = clamp(1 - grab.rt*1.5, 0, 1); ctx.strokeStyle = '#ffe066'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(ox, oy, 30 + grab.rt*120, 0, 7); ctx.stroke(); ctx.restore(); }
}
""")

# test hooks
R("get voltOk(){ return [voltOkT, voltOkFree]; },", "get turn(){ return turn && {t: turn.t, close: turn.close, zone: !!turn.zone}; }, get spdMul(){ return spdMul; }, get speedTier(){ return speedTier; }, get fastN(){ return actus.filter(a => a.fast && !a.got).length; }, get obsAhead(){ return obs.filter(o => o.kind === 'boat' && o.w > t && o.w < t + 4).map(o => +(o.w - t).toFixed(2)); }, get obsNear(){ return obs.filter(o => o.kind === 'boat' && Math.abs(o.w - t) < 4).map(o => +(o.w - t).toFixed(2)); },")
R(" voltWindow, doVolte,", " doVolte,")
open(f,'w').write(s); print('ok')
