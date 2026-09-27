
import os,json,re,tempfile
from openai import OpenAI
def client(): return OpenAI(api_key=os.getenv("OPENAI_API_KEY","").strip(),timeout=55.0,max_retries=1)
def model(): return os.getenv("OPENAI_MODEL","gpt-5.6-luna")
SYSTEM="""You are a demanding but supportive professional Italian teacher for a Persian-speaking A2 learner.
Use contemporary standard Italian. Persian explanations must be precise and readable. Correct strictly: do not give
credit for materially wrong grammar. Content must be high-frequency, practical and progressively harder."""
def ask(p,system=SYSTEM): return client().responses.create(model=model(),instructions=system,input=p).output_text
def jask(p, retries=2):
    last_error = None

    for attempt in range(retries + 1):
        try:
            extra = """
Return ONLY one valid JSON object.
Do not use Markdown or code fences.
Do not write anything before or after the JSON.
Use double quotes for all keys and string values.
Escape quotation marks inside strings correctly.
The response must be valid for Python json.loads().
"""
            t = ask(p + extra)
            t = t.strip()

            t = re.sub(r"^```(?:json)?\\s*", "", t)
            t = re.sub(r"\\s*```$", "", t)

            start = t.find("{")
            end = t.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise ValueError("No complete JSON object returned by AI.")

            clean = t[start:end + 1]
            return json.loads(clean)

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e

            if attempt < retries:
                continue

    raise RuntimeError(
        f"AI returned invalid JSON after {retries + 1} attempts: {last_error}"
    )
def vocab_batch(batch,avoid):
    return jask(f"""Daily vocabulary batch {batch}/5. Create exactly 10 HIGH-FREQUENCY Italian lexical WORDS for A2.
italian MUST be one word, not an expression. Mix useful verbs/nouns/adjectives/adverbs/connectors.
Avoid: {avoid[-80:]}. JSON {{"items":[{{"italian":"","article":"","pos":"","persian":"","example":""}}]}}""")["items"]
def idioms(avoid):
    return jask(f"""Create exactly 10 high-frequency everyday Italian expressions/chunks for A2-B1, useful in Italy.
Avoid: {avoid[-50:]}. JSON {{"items":[{{"expression":"","persian":"","use_fa":"","example":""}}]}}""")["items"]
def grammar_lesson(t,f):
    return jask(f"""Complete A2 lesson: {t}. Focus {f}. Structured for a graphical UI.
Persian explanation, Italian examples. JSON:
{{"overview":"","formula":"","uses":[{{"title":"","fa":"","it":""}}],
"rules":[{{"rule":"","example":"","meaning":""}}],"examples":[{{"it":"","fa":""}}],
"mistakes":[{{"wrong":"","right":"","why":""}}]}}""")
def grammar_exercises(t):
    return jask(f"""Create EXACTLY 10 progressively harder A2 exercises for {t}. Mix fill gap, transform, choose, correct error,
translate Persian->Italian. No answers. JSON {{"items":[{{"n":1,"type":"","q":""}}]}}""")["items"]
def grade(t,ex,ans):
    return jask(f"""STRICTLY grade these 10 A2 exercises on {t}. Exercises={json.dumps(ex,ensure_ascii=False)}
Answers={ans}. Score is integer 0-10, one point only for substantially correct answer.
JSON {{"score":0,"results":[{{"n":1,"ok":false,"answer":"","why_fa":""}}],"feedback_fa":"","review":[""]}}""")
def reading(day_no):
    return jask(f"""Create one ORIGINAL useful Italian reading for day {day_no} of an A2->B1 course.
Difficulty rises very gradually with day number. Topic must be practical/current-life (work, study, Italy, transport,
technology, health habits, culture, services); no fabricated breaking-news claims. 180-260 words.
JSON {{"title":"","level":"","text":"","words":[{{"it":"","fa":""}}],
"questions":[{{"q":""}}],"summary_fa":""}}""")
def writing_feedback(topic,text):
    return jask(f"""Topic={topic}\nText={text}\nCorrect STRICTLY for A2/B1. JSON:
{{"corrected":"","score":0,"errors":[{{"original":"","correct":"","why_fa":""}}],
"vocab_upgrades":[{{"old":"","better":""}}],"feedback_fa":""}}""")
def voice_reply(topic,hist,user):
    return jask(f"""Italian speaking practice topic {topic}. History={hist[-2500:]}. Learner={user}.
JSON {{"reply":"","correction_fa":"","better":"","question":""}}""")
def transcribe_audio(b):
    with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as f:f.write(b);p=f.name
    try:
        with open(p,"rb") as af:return client().audio.transcriptions.create(model=os.getenv("OPENAI_TRANSCRIBE_MODEL","gpt-4o-mini-transcribe"),file=af,language="it").text
    finally:
        try:os.remove(p)
        except:pass
def speech_bytes(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3",delete=False) as f:p=f.name
    try:
        with client().audio.speech.with_streaming_response.create(model=os.getenv("OPENAI_TTS_MODEL","gpt-4o-mini-tts"),
        voice=os.getenv("OPENAI_TTS_VOICE","alloy"),input=text,instructions="Natural clear standard Italian, slightly slow.") as r:r.stream_to_file(p)
        return open(p,"rb").read()
    finally:
        try:os.remove(p)
        except:pass


# ADD these functions to ai.py and use them instead of one-shot generation.

def vocab_batch_unique(batch, forbidden):
    forbidden = forbidden[-1500:]
    return jask(f"""Create exactly 10 HIGH-FREQUENCY A2 Italian WORDS.
Each italian field MUST contain exactly one lexical word, never a phrase.
ABSOLUTELY FORBIDDEN because already learned:
{json.dumps(forbidden,ensure_ascii=False)}
Do not return morphological/case variants merely to bypass duplication.
JSON: {{"items":[{{"italian":"","article":"","pos":"","persian":"","example":""}}]}}""")["items"]

def idioms_unique(forbidden):
    forbidden=forbidden[-1000:]
    return jask(f"""Create exactly 10 practical everyday Italian expressions for A2-B1.
Never repeat or trivially rephrase anything in this learned list:
{json.dumps(forbidden,ensure_ascii=False)}
JSON: {{"items":[{{"expression":"","persian":"","use_fa":"","example":""}}]}}""")["items"]

def reading_unique(day_no, old_titles):
    return jask(f"""Create one ORIGINAL Italian learning text for course day {day_no}.
Difficulty must rise gradually from A2 toward B1. Use useful real-life themes.
Do NOT repeat these previous titles/topics:
{json.dumps(old_titles[-300:],ensure_ascii=False)}
Do not invent breaking-news facts. 180-280 words.
JSON: {{"title":"","level":"","text":"","words":[{{"it":"","fa":""}}],
"questions":[{{"q":""}}],"summary_fa":""}}""")
