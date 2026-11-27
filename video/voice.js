// Озвучка нейроголосом «Светлана» (edge-tts из maker/tutorials/.venv): node voice.js <id> → build/<id>/voice/iNN.wav + voice.json
const { execSync } = require('child_process');
const fs = require('fs');
const TTS = '/Users/kate/Documents/Проекты/frontpupirka/maker/tutorials/.venv/bin/edge-tts';
const V = require('./steps.js')[process.argv[2]];
const dir = `build/${process.argv[2]}/voice`;
const VOICE = V.voice || 'ru-RU-SvetlanaNeural', RATE = V.rate || '+5%';
fs.mkdirSync(dir, { recursive: true });
const lines = [V.intro].concat(V.steps.map(s => s.say)).concat(V.outroSay ? [V.outroSay] : []);
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const out = [];
lines.forEach((t, i) => {
  const base = `${dir}/i${String(i).padStart(2, '0')}`;
  // как читать: Ordo – «Ордо», ИИ – «и-и», Jira – «Джира», ГОК – «гок», PDF – «пэ-дэ-эф»
  const say = t.replace(/[«»]/g, '').replace(/Ordo/g, 'Ордо').replace(/(^|[^А-Яа-я])ИИ(?![А-Яа-я])/g, '$1И-И').replace(/Jira/g, 'Джира')
    .replace(/ГОКе/g, 'гоке').replace(/PDF/g, 'пэ-дэ-эф').replace(/план-факт/g, 'план факт');
  const key = VOICE + '|' + RATE + '|' + say;
  const done = fs.existsSync(base + '.wav') && fs.existsSync(base + '.key') && fs.readFileSync(base + '.key', 'utf8') === key;
  if (!done) { fs.writeFileSync(base + '.txt', say); fs.writeFileSync(base + '.key', key); }
  for (let k = 0; !done; k++) {
    try { execSync(`"${TTS}" --voice ${VOICE} --rate=${RATE} -f "${base}.txt" --write-media "${base}.mp3"`, { stdio: 'ignore' }); if (fs.statSync(base + '.mp3').size > 1000) break; } catch (e) {}
    if (k >= 8) throw new Error('озвучка не получилась: ' + base);
    sleep(5000 * (k + 1));
  }
  if (!done) execSync(`ffmpeg -y -loglevel error -i "${base}.mp3" -af "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse" -ar 48000 -ac 1 "${base}.wav"`);
  const d = parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${base}.wav"`).toString());
  out.push({ file: base.split('/').pop() + '.wav', text: t, dur: d });
});
fs.writeFileSync(`${dir}/voice.json`, JSON.stringify(out, null, 1));
console.log(out.map(x => x.dur.toFixed(1)).join(' '), '· всего', out.reduce((a, x) => a + x.dur, 0).toFixed(1));
