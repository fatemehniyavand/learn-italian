import os, html, json
from datetime import date, datetime, timedelta
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
from db import *
from ai import *
from curriculum import *
from full_history import *
from report import make_report

st.set_page_config(page_title="Italian Coach • A2→B1", page_icon="🇮🇹", layout="wide", initial_sidebar_state="expanded")
init_db()
init_history_tables()
init_full_history()

TODAY = date.today().isoformat()

st.markdown("""<style>
:root{--ink:#0f172a;--muted:#475569;--line:#d7dee8;--nav:#0b2744;--blue:#155eef;--paper:#fff;--bg:#f3f6fa}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1280px;padding:1.6rem 2.2rem 4rem}
[data-testid="stSidebar"]{background:var(--nav)}
[data-testid="stSidebar"] *{color:#fff!important}
[data-testid="stSidebar"] label{font-weight:700}
h1,h2,h3,h4,p,span,label{color:var(--ink)}
.hero{background:#fff;border:1px solid var(--line);border-radius:24px;padding:26px 30px;margin-bottom:22px;box-shadow:0 8px 28px rgba(16,42,67,.06)}
.hero h1{margin:0;color:#0b2744;font-size:2.05rem}.hero p{color:var(--muted);margin:.45rem 0 0;font-size:1.02rem}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin:9px 0;box-shadow:0 4px 16px rgba(16,42,67,.04)}
.rtl{direction:rtl;text-align:right;font-family:Tahoma,"Segoe UI",Arial,sans-serif;line-height:2;color:#172033;font-size:1rem}
.word{font-size:2.25rem;font-weight:800;color:#0b2744}.small{color:var(--muted)}
.step{display:inline-block;background:#e8f0ff;color:#174ea6;padding:5px 10px;border-radius:99px;font-weight:800;font-size:.78rem}
.done{display:inline-block;background:#dcfce7;color:#166534;padding:5px 10px;border-radius:99px;font-weight:800;font-size:.78rem}
div.stButton>button{background:#155eef!important;color:#fff!important;border:0!important;border-radius:11px!important;font-weight:750!important;min-height:44px}
div.stButton>button:hover{background:#0b4bd4!important;color:#fff!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:16px;padding:13px}
[data-testid="stDataFrame"]{background:#fff;border-radius:14px}
.stTabs [data-baseweb="tab"]{font-weight:750;color:#26374a}
</style>""", unsafe_allow_html=True)

MENU=[
"🏠 00 • Dashboard","🧠 01 • 50 کلمه","💬 02 • 10 اصطلاح","📘 03 • گرامر",
"📝 04 • تمرین گرامر","📖 05 • متن روز","✍️ 06 • انشا","🗣️ 07 • مکالمه",
"🎯 08 • مرور","📅 09 • پیشرفت","🗄️ 10 • آرشیو کامل"
]
page=st.sidebar.radio("🇮🇹 ITALIAN COACH",MENU)

t=today_row()
done=sum(t.get(x,0) for x in SECTIONS)
st.sidebar.markdown("---")
st.sidebar.progress(done/len(SECTIONS))
st.sidebar.write(f"امروز: **{done}/{len(SECTIONS)}** • 🔥 **{streak()} روز**")
st.sidebar.caption(f"📅 {TODAY}")

def hero(a,b):
    st.markdown(f'<div class="hero"><h1>{a}</h1><p>{b}</p></div>',unsafe_allow_html=True)

def keycheck():
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")=="put_your_key_here":
        st.error("API key تنظیم نشده است.")
        st.stop()

def safe(fn,*args):
    try:
        return fn(*args)
    except Exception as e:
        st.error(f"درخواست کامل نشد: {type(e).__name__}: {e}")
        return None

def course_day():
    rows=progress(365)
    return max(1,sum(1 for r in rows if any(r[k] for k in SECTIONS)))

def archive_once(section, content, subtype="", title="", source_key=""):
    try:
        archive_content(section,content,subtype=subtype,title=title,source_key=source_key)
    except Exception:
        pass

def show_last_correction(section,ref):
    row=latest_correction(section,str(ref))
    if not row:
        return
    r=json.loads(row["payload"])
    st.markdown("### نتیجهٔ ذخیره‌شده")
    if row["user_answer"]:
        with st.expander("📝 جواب من",expanded=True):
            st.write(row["user_answer"])
    if r.get("score") is not None:
        st.metric("نمره",f'{r.get("score",row["score"])}/10')
    if r.get("corrected"):
        st.markdown("#### نسخه اصلاح‌شده")
        st.success(r["corrected"])
    for q in r.get("results",[]):
        st.write(("✅" if q.get("ok") else "❌"),f'**{q.get("n","")}**',q.get("answer",""),"—",q.get("why_fa",""))
    for e in r.get("errors",[]):
        st.error(f'{e.get("original","")} → {e.get("correct","")}\n\n{e.get("why_fa","")}')
    if r.get("feedback_fa"):
        st.markdown(f"<div class='card rtl'>{html.escape(r['feedback_fa'])}</div>",unsafe_allow_html=True)

if page.startswith("🏠"):
    hero("مسیر امروز","یک دورهٔ مرتب و ماندگار؛ تولیدات، جواب‌ها و اصلاحات در دیتابیس ذخیره می‌شوند.")
    labels=[("01","50 کلمه","vocab"),("02","10 اصطلاح","idioms"),("03","گرامر","grammar"),
            ("04","تمرین","exercises"),("05","متن","reading"),("06","انشا","writing"),
            ("07","مکالمه","speaking"),("08","مرور","review")]
    cs=st.columns(4)
    for i,(n,l,k) in enumerate(labels):
        cs[i%4].metric(f"{n} • {l}","✓ انجام شد" if t.get(k) else "در انتظار")
    st.progress(done/8)
    st.subheader("ترتیب دوره")
    st.markdown("**کلمه → اصطلاح → گرامر → تمرین → متن روز → انشا → مکالمه → مرور**")
    st.info("هر محتوایی که تولید یا تصحیح شود با تاریخ ذخیره می‌شود. تغییر صفحه یا Refresh آن را حذف نمی‌کند.")
    acts=activity_today()
    if acts:
        st.dataframe(pd.DataFrame([dict(x) for x in acts])[["ts","section","action","detail"]],
                     use_container_width=True,hide_index=True)

elif page.startswith("🧠"):
    keycheck()
    hero("01 • 50 کلمه روز","۵۰ کلمهٔ پرکاربرد، بدون تکرار از روزهای قبل؛ ۵ بستهٔ ۱۰تایی.")
    words=items_for_day(TODAY,"vocab")
    if not words:
        words=get_daily("vocab") or []
        if words:
            saved=save_unique_items(TODAY,"vocab",words,"italian")
            words=items_for_day(TODAY,"vocab") or saved or words
            archive_once("vocab",words,"daily_words","50 parole",TODAY)
    if not words:
        if st.button("ساخت 50 کلمه امروز",type="primary",key="make_vocab"):
            forbidden=learned_values("vocab")
            bar=st.progress(0,"شروع تولید...")
            for batch in range(1,6):
                need=10
                tries=0
                while need>0 and tries<6:
                    bar.progress((batch-1)/5,f"بسته {batch}/5 • {10-need}/10")
                    cand=safe(vocab_batch_unique,batch,forbidden)
                    if not cand: break
                    accepted=save_unique_items(TODAY,"vocab",cand,"italian")
                    forbidden.extend(normalize_text(x["italian"]) for x in accepted)
                    current=items_for_day(TODAY,"vocab")
                    need=max(0,batch*10-len(current))
                    tries+=1
                if need>0:
                    st.warning(f"بسته {batch} کامل نشد؛ دوباره دکمه را بزن تا فقط موارد جدید تکمیل شوند.")
                    break
            words=items_for_day(TODAY,"vocab")
            if words:
                put_daily("vocab",words)
                archive_once("vocab",words,"daily_words","50 parole",TODAY)
                log("vocab","unique words generated",2,f"{len(words)} words")
            st.rerun()
    if words:
        st.caption(f"ذخیره‌شده امروز: {len(words)}/50")
        max_batch=max(1,(len(words)+9)//10)
        batch=st.radio("بسته",range(1,max_batch+1),horizontal=True,
                       format_func=lambda x:f"{x} · {(x-1)*10+1}-{min(x*10,len(words))}",key="vocab_batch")
        for i,w in enumerate(words[(batch-1)*10:batch*10],(batch-1)*10+1):
            with st.expander(f"{i:02d} • {w['italian']}"):
                st.markdown(f"<div class='card'><div class='word'>{html.escape(w['italian'])}</div>"
                            f"<span class='small'>{html.escape(w.get('article',''))} · {html.escape(w.get('pos',''))}</span></div>",
                            unsafe_allow_html=True)
                st.markdown(f"<div class='rtl'><b>{html.escape(w.get('persian',''))}</b></div>",unsafe_allow_html=True)
                st.write("مثال:",w.get("example",""))
        if len(words)>=50 and not t.get("vocab"):
            if st.button("✓ واژگان امروز را تمام کردم",key="done_vocab"):
                mark("vocab","50 unique words completed",50);st.rerun()
        elif t.get("vocab"): st.success("✓ واژگان امروز ثبت شده است.")

elif page.startswith("💬"):
    keycheck()
    hero("02 • 10 اصطلاح روز","۱۰ عبارت کاربردی؛ موارد روزهای قبل دوباره پذیرفته نمی‌شوند.")
    items=items_for_day(TODAY,"idiom")
    if not items:
        old=get_daily("idioms") or []
        if old:
            save_unique_items(TODAY,"idiom",old,"expression")
            items=items_for_day(TODAY,"idiom") or old
            archive_once("idioms",items,"daily_expressions","10 espressioni",TODAY)
    if len(items)<10 and st.button("تکمیل 10 اصطلاح امروز",type="primary",key="make_idioms"):
        forbidden=learned_values("idiom");tries=0
        while len(items_for_day(TODAY,"idiom"))<10 and tries<7:
            cand=safe(idioms_unique,forbidden)
            if not cand: break
            accepted=save_unique_items(TODAY,"idiom",cand,"expression")
            forbidden.extend(normalize_text(x["expression"]) for x in accepted);tries+=1
        items=items_for_day(TODAY,"idiom")[:10]
        put_daily("idioms",items);archive_once("idioms",items,"daily_expressions","10 espressioni",TODAY)
        log("idioms","unique expressions generated",2,f"{len(items)} expressions");st.rerun()
    for i,x in enumerate(items,1):
        with st.expander(f"{i:02d} • {x['expression']}"):
            st.markdown(f"<div class='rtl'><b>معنی:</b> {html.escape(x.get('persian',''))}<br>"
                        f"<b>کاربرد:</b> {html.escape(x.get('use_fa',''))}</div>",unsafe_allow_html=True)
            st.write("🇮🇹",x.get("example",""))
    if len(items)>=10 and not t.get("idioms"):
        if st.button("✓ اصطلاحات امروز تمام شد",key="done_idioms"):
            mark("idioms","10 unique expressions completed",10);st.rerun()
    elif t.get("idioms"): st.success("✓ اصطلاحات امروز ثبت شده است.")

elif page.startswith("📘"):
    keycheck()
    hero("03 • گرامر A2","فهرست کامل و مرتب A2؛ هر Unit یک بار ساخته و دائماً نگهداری می‌شود.")
    gs=grammar_status();doneg=sum(1 for v in gs.values() if v["status"]=="completed")
    st.progress(doneg/len(GRAMMAR_A2));st.caption(f"{doneg}/{len(GRAMMAR_A2)} Unit تمرین‌شده")
    u=st.selectbox("فهرست کامل گرامر A2",range(len(GRAMMAR_A2)),
        format_func=lambda i:f"{'✓' if gs.get(i+1,{}).get('status')=='completed' else '○'} {i+1:02d} · {GRAMMAR_A2[i]['title']} — {GRAMMAR_A2[i]['group']}",
        key="grammar_unit")
    g=GRAMMAR_A2[u];L=get_lesson(g["unit"])
    if not L and st.button("ساخت درس",type="primary",key=f"lesson_{g['unit']}"):
        L=safe(grammar_lesson,g["title"],g["focus"])
        if L:
            put_lesson(g["unit"],L);archive_once("grammar",L,"lesson",g["title"],str(g["unit"]))
            log("grammar","lesson generated",1,str(g["unit"]));st.rerun()
    if L:
        archive_once("grammar",L,"lesson",g["title"],str(g["unit"]))
        st.markdown(f"<div class='card'><span class='step'>UNIT {g['unit']:02d}</span><h2>{g['title']}</h2>"
                    f"<div class='rtl'>{html.escape(L.get('overview',''))}</div><hr><b>Formula</b><p>{html.escape(L.get('formula',''))}</p></div>",
                    unsafe_allow_html=True)
        st.subheader("کاربردها")
        for x in L.get("uses",[]):
            st.markdown(f"<div class='card'><b>{html.escape(x.get('title',''))}</b>"
                        f"<div class='rtl'>{html.escape(x.get('fa',''))}</div><p>🇮🇹 {html.escape(x.get('it',''))}</p></div>",
                        unsafe_allow_html=True)
        st.subheader("قواعد")
        st.dataframe(pd.DataFrame(L.get("rules",[])),use_container_width=True,hide_index=True)
        st.subheader("مثال‌ها")
        for x in L.get("examples",[]):
            st.markdown(f"<div class='card'><b>🇮🇹 {html.escape(x.get('it',''))}</b>"
                        f"<div class='rtl'>🇮🇷 {html.escape(x.get('fa',''))}</div></div>",unsafe_allow_html=True)
        st.subheader("اشتباهات رایج")
        for x in L.get("mistakes",[]): st.error(f"❌ {x.get('wrong','')} → ✅ {x.get('right','')}\n\n{x.get('why','')}")
        if not t.get("grammar"):
            if st.button("✓ درس را مطالعه کردم",key=f"done_lesson_{g['unit']}"):
                mark("grammar","lesson studied",5,f"Unit {g['unit']}");st.rerun()

elif page.startswith("📝"):
    keycheck()
    hero("04 • تمرین گرامر","سؤال، جواب، تصحیح و نمره همگی ذخیره می‌شوند و بعد از کلیک محو نمی‌شوند.")
    u=st.selectbox("Unit تمرین",range(len(GRAMMAR_A2)),
                   format_func=lambda i:f"{i+1:02d} · {GRAMMAR_A2[i]['title']}",key="exercise_unit")
    g=GRAMMAR_A2[u];kind=f"grammar_ex_{g['unit']}";ex=get_daily(kind)
    if not ex and st.button("ساخت 10 تمرین",type="primary",key=f"make_ex_{g['unit']}"):
        ex=safe(grammar_exercises,g["title"])
        if ex:
            put_daily(kind,ex);archive_once("grammar_exercises",ex,"questions",g["title"],str(g["unit"]))
            log("exercises","questions generated",1,f"Unit {g['unit']}");st.rerun()
    if ex:
        archive_once("grammar_exercises",ex,"questions",g["title"],str(g["unit"]))
        for x in ex: st.markdown(f"**{x['n']}. [{x['type']}]** {x['q']}")
        ans=st.text_area("جواب 1 تا 10",height=230,key=f"answers_{TODAY}_{g['unit']}",
                         placeholder="1) ...\n2) ...\n...\n10) ...")
        if st.button("تصحیح سخت‌گیرانه",type="primary",key=f"grade_{g['unit']}") and ans.strip():
            r=safe(grade,g["title"],ex,ans)
            if r:
                save_attempt("grammar",g["unit"],ans,r,int(r.get("score",0)))
                set_grammar_score(g["unit"],int(r.get("score",0)))
                archive_correction("grammar_exercises",json.dumps(ex,ensure_ascii=False),ans,r,
                                   ref=g["unit"],score=r.get("score",0))
                mark("exercises","grammar exercises",10,f"Unit {g['unit']} · {r.get('score',0)}/10")
                st.rerun()
        show_last_correction("grammar_exercises",g["unit"])
        hist=[dict(x) for x in attempts("grammar") if x["ref"]==str(g["unit"])]
        if hist:
            st.subheader("تاریخچه تلاش‌ها")
            st.dataframe(pd.DataFrame(hist)[["day","score","ts"]],use_container_width=True,hide_index=True)

elif page.startswith("📖"):
    keycheck()
    hero("05 • متن روز","هر روز یک متن جدید و ذخیره‌شده؛ سطح به‌تدریج از A2 به B1 نزدیک می‌شود.")
    R=reading_for_day(TODAY) or get_daily("reading")
    if R and not reading_for_day(TODAY):
        save_reading_unique(TODAY,R)
    if not R and st.button("ساخت متن امروز",type="primary",key="make_reading"):
        for _ in range(5):
            candidate=safe(reading_unique,course_day(),reading_titles())
            if candidate and save_reading_unique(TODAY,candidate):
                R=candidate;put_daily("reading",R)
                archive_once("reading",R,"daily_text",R.get("title",""),TODAY)
                log("reading","daily reading generated",2,R.get("level",""));break
        st.rerun()
    if R:
        archive_once("reading",R,"daily_text",R.get("title",""),TODAY)
        st.markdown(f"<div class='card'><span class='step'>{html.escape(R.get('level',''))}</span>"
                    f"<h2>{html.escape(R.get('title',''))}</h2><p style='font-size:1.12rem;line-height:2'>{html.escape(R.get('text',''))}</p></div>",
                    unsafe_allow_html=True)
        st.subheader("واژه‌های مهم")
        st.dataframe(pd.DataFrame(R.get("words",[])),use_container_width=True,hide_index=True)
        with st.expander("خلاصه فارسی"):
            st.markdown(f"<div class='rtl'>{html.escape(R.get('summary_fa',''))}</div>",unsafe_allow_html=True)
        st.subheader("درک مطلب")
        for i,q in enumerate(R.get("questions",[]),1): st.write(i,q.get("q",""))
        if not t.get("reading") and st.button("✓ متن امروز را خواندم",key="done_reading"):
            mark("reading","daily reading completed",10,R.get("level",""));st.rerun()
        elif t.get("reading"): st.success("✓ Reading امروز ثبت شده است.")

elif page.startswith("✍️"):
    keycheck()
    hero("06 • انشا","موضوع‌ها مرتب سخت‌تر می‌شوند؛ متن اصلی و تمام اصلاحات دائماً ذخیره می‌شوند.")
    idx=(course_day()-1)%len(WRITING_TOPICS);topic=WRITING_TOPICS[idx]
    archive_once("writing",{"topic":topic},"prompt",topic,topic)
    st.markdown(f"<div class='card'><span class='step'>TOPIC {idx+1:02d}</span><h3>{html.escape(topic)}</h3></div>",unsafe_allow_html=True)
    text=st.text_area("ایتالیایی بنویس",height=260,key=f"writing_{TODAY}_{idx}")
    if st.button("تصحیح سخت‌گیرانه",type="primary",key=f"grade_writing_{idx}") and text.strip():
        r=safe(writing_feedback,topic,text)
        if r:
            save_journal(topic,text,r.get("corrected",""),json.dumps(r,ensure_ascii=False),int(r.get("score",0)))
            archive_correction("writing",topic,text,r,ref=topic,score=r.get("score",0))
            mark("writing","writing corrected",10,f'{r.get("score",0)}/10')
            st.rerun()
    show_last_correction("writing",topic)

elif page.startswith("🗣️"):
    keycheck()
    hero("07 • مکالمه","هر نوبت مکالمه، متن شنیده‌شده و پاسخ مدرس ذخیره می‌شود.")
    topic=CONVERSATION_TOPICS[(course_day()-1)%len(CONVERSATION_TOPICS)]
    st.write("موضوع امروز:",f"**{topic}**")
    audio=st.audio_input("🎤 ایتالیایی صحبت کن",key="voice_today")
    if audio:
        sig=f"{TODAY}-{len(audio.getvalue())}"
        if st.session_state.get("sig")!=sig:
            st.session_state.sig=sig
            tr=safe(transcribe_audio,audio.getvalue())
            if tr:
                r=safe(voice_reply,topic,"",tr)
                if r:
                    spoken=(r.get("reply","")+" "+r.get("question","")).strip()
                    save_speaking(topic,tr,spoken)
                    archive_once("speaking",{"user":tr,"tutor":spoken,"correction_fa":r.get("correction_fa",""),
                                            "better":r.get("better",""),"topic":topic},
                                 "turn",topic,datetime.now().isoformat())
                    mark("speaking","voice session",5,topic)
                    st.session_state["last_voice"]={"tr":tr,"spoken":spoken,"r":r}
    last=st.session_state.get("last_voice")
    if last:
        st.write("**شنیدم:**",last["tr"]);st.success(last["spoken"])
        st.info("اصلاح: "+last["r"].get("correction_fa","")+"\n\nنسخه بهتر: "+last["r"].get("better",""))
        if st.button("🔊 پخش پاسخ",key="tts_last"):
            audio_bytes=safe(speech_bytes,last["spoken"])
            if audio_bytes: st.audio(audio_bytes,format="audio/mp3",autoplay=True)

elif page.startswith("🎯"):
    hero("08 • مرور روز","چک نهایی مسیر روزانه.")
    t=today_row()
    labels=[("واژگان","vocab"),("اصطلاحات","idioms"),("گرامر","grammar"),("تمرین","exercises"),
            ("متن","reading"),("انشا","writing"),("مکالمه","speaking")]
    for l,k in labels: st.write("✅" if t.get(k) else "⬜",l)
    if not t.get("review") and st.button("ثبت پایان مطالعه امروز",type="primary",key="finish_day"):
        mark("review","daily review completed",10);st.balloons();st.rerun()
    elif t.get("review"): st.success("✓ مرور امروز ثبت شده است.")

elif page.startswith("📅"):
    hero("09 • پیشرفت و گزارش PDF","تقویم، نمرات و گزارش قابل دانلود از فعالیت‌های ذخیره‌شده.")
    rows=[dict(x) for x in progress(365)];df=pd.DataFrame(rows)
    if not df.empty:
        df["total"]=df[SECTIONS].sum(axis=1);df["percent"]=(df["total"]/len(SECTIONS)*100).round()
        a,b,c=st.columns(3)
        a.metric("Streak",f"{streak()} روز");b.metric("روزهای فعال",int((df.total>0).sum()));c.metric("امروز",f"{int(df.iloc[0].percent)}%")
        st.line_chart(df.sort_values("day").set_index("day")["percent"])
        show=df[["day"]+SECTIONS+["percent"]].copy()
        for k in SECTIONS: show[k]=show[k].map({1:"✓",0:"—"})
        st.dataframe(show,use_container_width=True,hide_index=True)
    st.subheader("نتایج گرامر")
    gs=grammar_status()
    data=[{"Unit":g["unit"],"Grammar":g["title"],"Status":gs.get(g["unit"],{}).get("status","not_started"),
           "Best /10":gs.get(g["unit"],{}).get("best_score",0),"Attempts":gs.get(g["unit"],{}).get("attempts",0)}
          for g in GRAMMAR_A2]
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
    st.subheader("دانلود گزارش")
    c1,c2=st.columns(2)
    start=c1.date_input("از تاریخ",value=date.today()-timedelta(days=30),key="pdf_start")
    end=c2.date_input("تا تاریخ",value=date.today(),key="pdf_end")
    if start<=end:
        try:
            pdf=make_report(str(start),str(end))
            st.download_button("⬇️ دانلود گزارش PDF",data=pdf,
                file_name=f"italian_report_{start}_{end}.pdf",mime="application/pdf",key="download_pdf")
        except Exception as e:
            st.error(f"ساخت PDF ناموفق بود: {e}")

elif page.startswith("🗄️"):
    hero("10 • آرشیو کامل","تمام محتوای تولیدشده، جواب‌ها، اصلاحات و نمرات بعداً قابل مشاهده‌اند.")
    options=["همه","vocab","idioms","grammar","grammar_exercises","reading","writing","speaking"]
    section=st.selectbox("فیلتر بخش",options,key="archive_filter")
    sec=None if section=="همه" else section
    rows=archive_rows(sec)
    st.subheader("محتوای ذخیره‌شده")
    if rows:
        summary=pd.DataFrame([{"ID":x["id"],"تاریخ":x["day"],"بخش":x["section"],"نوع":x["subtype"],
                               "عنوان":x["title"],"زمان":x["created_at"]} for x in rows])
        st.dataframe(summary,use_container_width=True,hide_index=True)
        ids=[x["id"] for x in rows]
        chosen=st.selectbox("باز کردن محتوای کامل",ids,
            format_func=lambda i:next((f'#{x["id"]} • {x["day"]} • {x["section"]} • {x["title"]}' for x in rows if x["id"]==i),str(i)),
            key="archive_item")
        row=next(x for x in rows if x["id"]==chosen)
        with st.expander("نمایش محتوای کامل",expanded=True):
            try: st.json(json.loads(row["content"]),expanded=True)
            except: st.write(row["content"])
    else: st.info("هنوز محتوایی در این بخش ذخیره نشده است.")

    st.subheader("جواب‌ها و اصلاحات")
    corr=correction_rows(sec)
    if corr:
        cdf=pd.DataFrame([{"ID":x["id"],"تاریخ":x["day"],"بخش":x["section"],"مرجع":x["ref"],
                           "جواب من":x["user_answer"],"نسخه اصلاح‌شده":x["corrected"],
                           "نمره":x["score"],"زمان":x["created_at"]} for x in corr])
        st.dataframe(cdf,use_container_width=True,hide_index=True)
        cids=[x["id"] for x in corr]
        cid=st.selectbox("باز کردن اصلاح کامل",cids,key="correction_item")
        cr=next(x for x in corr if x["id"]==cid)
        with st.expander("جزئیات کامل اصلاح",expanded=True):
            st.markdown("**متن/سؤال:**");st.write(cr["prompt"])
            st.markdown("**جواب من:**");st.write(cr["user_answer"])
            try: st.json(json.loads(cr["payload"]),expanded=True)
            except: st.write(cr["payload"])
    else: st.info("هنوز اصلاح ذخیره‌شده‌ای در این فیلتر وجود ندارد.")
