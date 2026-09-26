
import os,html,json
from datetime import date
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from db import *
from ai import *
from curriculum import *
st.set_page_config(page_title="Italian Coach • A2→B1",page_icon="🇮🇹",layout="wide",initial_sidebar_state="expanded")
init_db()
st.markdown("""<style>
:root{--ink:#111827;--muted:#526071;--line:#d8e0ea;--nav:#102a43;--blue:#155eef;--paper:#ffffff;--bg:#f3f6fa}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
.stApp{background:var(--bg);color:var(--ink)} .block-container{max-width:1280px;padding:1.6rem 2.2rem 4rem}
[data-testid="stSidebar"]{background:#102a43} [data-testid="stSidebar"] *{color:#f8fafc!important}
[data-testid="stSidebar"] label{font-weight:650}
h1,h2,h3,p,span,label{color:var(--ink)} .hero{background:#fff;border:1px solid var(--line);border-radius:24px;
padding:26px 30px;margin-bottom:22px;box-shadow:0 8px 28px rgba(16,42,67,.06)}
.hero h1{margin:0;color:#102a43;font-size:2.05rem}.hero p{color:#526071;margin:.45rem 0 0;font-size:1.02rem}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin:9px 0;box-shadow:0 4px 16px rgba(16,42,67,.04)}
.rtl{direction:rtl;text-align:right;font-family:Tahoma,"Segoe UI",Arial,sans-serif;line-height:2;color:#172033}
.word{font-size:2.7rem;font-weight:800;color:#102a43}.small{color:#526071}
.step{display:inline-block;background:#e8f0ff;color:#174ea6;padding:5px 10px;border-radius:99px;font-weight:700;font-size:.78rem}
div.stButton>button{background:#155eef!important;color:white!important;border:0!important;border-radius:11px!important;font-weight:700!important;min-height:44px}
div.stButton>button:hover{background:#0b4bd4!important;color:#fff!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:16px;padding:13px}
.stTabs [data-baseweb="tab"]{font-weight:700;color:#26374a}
</style>""",unsafe_allow_html=True)

MENU=["🏠 00 • Dashboard","🧠 01 • 50 کلمه","💬 02 • 10 اصطلاح","📘 03 • گرامر",
"📝 04 • تمرین گرامر","📖 05 • متن روز","✍️ 06 • انشا","🗣️ 07 • مکالمه","🎯 08 • مرور","📅 09 • پیشرفت"]
page=st.sidebar.radio("🇮🇹 ITALIAN COACH",MENU)
st.sidebar.markdown("---"); t=today_row(); done=sum(t.get(x,0) for x in SECTIONS)
st.sidebar.progress(done/len(SECTIONS)); st.sidebar.write(f"امروز: **{done}/{len(SECTIONS)}** • 🔥 **{streak()} روز**")
def hero(a,b):st.markdown(f'<div class="hero"><h1>{a}</h1><p>{b}</p></div>',unsafe_allow_html=True)
def keycheck():
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")=="put_your_key_here":st.error("API key در .env تنظیم نشده.");st.stop()
def safe(fn,*args):
    try:return fn(*args)
    except Exception as e:st.error(f"درخواست کامل نشد: {type(e).__name__}: {e}");return None
def course_day():
    rows=progress(365); return max(1,sum(1 for r in rows if any(r[k] for k in SECTIONS)))

if page.startswith("🏠"):
    hero("مسیر امروز","یک مسیر ثابت و منظم؛ محتوای امروز با جابه‌جایی بین صفحات از بین نمی‌رود.")
    labels=[("01","50 کلمه","vocab"),("02","10 اصطلاح","idioms"),("03","گرامر","grammar"),("04","تمرین","exercises"),
    ("05","متن","reading"),("06","انشا","writing"),("07","مکالمه","speaking"),("08","مرور","review")]
    cs=st.columns(4)
    for i,(n,l,k) in enumerate(labels):
        cs[i%4].metric(f"{n} • {l}","✓ انجام شد" if t.get(k) else "در انتظار")
    st.progress(done/8); st.subheader("ترتیب دوره")
    st.markdown("**کلمه → اصطلاح → گرامر → تمرین → متن روز → انشا → مکالمه → مرور**")
    st.info("هر چیزی که امروز تولید یا تصحیح شود در دیتابیس ذخیره می‌شود. فردا محتوای روز جدید ساخته می‌شود.")
    acts=activity_today()
    if acts:st.dataframe(pd.DataFrame([dict(x) for x in acts])[["ts","section","action","detail"]],use_container_width=True,hide_index=True)

elif page.startswith("🧠"):
    keycheck();hero("01 • 50 کلمه روز","فقط کلمه؛ ۵ بسته ۱۰تایی. معنی و مثال پشت کارت است.")
    words=get_daily("vocab") or []
    if not words and st.button("ساخت 50 کلمه امروز",type="primary"):
        allw=[]; bar=st.progress(0,"شروع...")
        for b in range(1,6):
            bar.progress((b-1)/5,f"بسته {b}/5...")
            x=safe(vocab_batch,b,[w["italian"] for w in allw])
            if not x:break
            allw+=x
        if len(allw)==50:put_daily("vocab",allw);words=allw;log("vocab","50 words generated",2);bar.progress(1,"آماده ✓")
    if words:
        batch=st.radio("بسته",range(1,6),horizontal=True,format_func=lambda x:f"{x} · {(x-1)*10+1}-{x*10}")
        for i,w in enumerate(words[(batch-1)*10:batch*10],(batch-1)*10+1):
            with st.expander(f"{i:02d}  •  {w['italian']}"):
                st.markdown(f"<div class='card'><div class='word'>{html.escape(w['italian'])}</div><span class='small'>{html.escape(w.get('article',''))} · {html.escape(w.get('pos',''))}</span></div>",unsafe_allow_html=True)
                st.markdown(f"<div class='rtl'><b>{html.escape(w['persian'])}</b></div>",unsafe_allow_html=True);st.write("مثال:",w["example"])
        if st.button("✓ واژگان امروز را تمام کردم"):mark("vocab","50 words completed",50);st.rerun()

elif page.startswith("💬"):
    keycheck();hero("02 • 10 اصطلاح روز","عبارت‌های پرکاربرد مکالمه؛ معنی، کاربرد و مثال.")
    items=get_daily("idioms") or []
    if not items and st.button("ساخت 10 اصطلاح امروز",type="primary"):
        x=safe(idioms,[]); 
        if x:put_daily("idioms",x);items=x;log("idioms","10 expressions generated",2)
    for i,x in enumerate(items,1):
        with st.expander(f"{i:02d} • {x['expression']}"):
            st.markdown(f"<div class='rtl'><b>معنی:</b> {x['persian']}<br><b>کاربرد:</b> {x['use_fa']}</div>",unsafe_allow_html=True);st.write("🇮🇹",x["example"])
    if items and st.button("✓ اصطلاحات امروز تمام شد"):mark("idioms","10 expressions completed",10);st.rerun()

elif page.startswith("📘"):
    keycheck();hero("03 • گرامر A2","۳۲ درس مرتب؛ هر درس یک بار ساخته و برای همیشه ذخیره می‌شود.")
    gs=grammar_status(); doneg=sum(1 for v in gs.values() if v["status"]=="completed")
    st.progress(doneg/len(GRAMMAR_A2));st.caption(f"{doneg}/{len(GRAMMAR_A2)} درس تمرین‌شده")
    u=st.selectbox("فهرست کامل گرامر A2",range(len(GRAMMAR_A2)),format_func=lambda i:f"{'✓' if gs.get(i+1,{}).get('status')=='completed' else '○'} {i+1:02d} · {GRAMMAR_A2[i]['title']} — {GRAMMAR_A2[i]['group']}")
    g=GRAMMAR_A2[u];L=get_lesson(g["unit"])
    if not L and st.button("باز کردن / ساخت این درس",type="primary"):
        L=safe(grammar_lesson,g["title"],g["focus"])
        if L:put_lesson(g["unit"],L);log("grammar","lesson generated",1,str(g["unit"]))
    if L:
        st.markdown(f"<div class='card'><span class='step'>UNIT {g['unit']:02d}</span><h2>{g['title']}</h2><div class='rtl'>{L['overview']}</div><hr><b>Formula</b><p>{L['formula']}</p></div>",unsafe_allow_html=True)
        st.subheader("کاربردها")
        for x in L["uses"]:st.markdown(f"<div class='card'><b>{x['title']}</b><div class='rtl'>{x['fa']}</div><p>🇮🇹 {x['it']}</p></div>",unsafe_allow_html=True)
        st.subheader("قواعد");st.dataframe(pd.DataFrame(L["rules"]),use_container_width=True,hide_index=True)
        st.subheader("مثال‌ها")
        for x in L["examples"]:st.markdown(f"<div class='card'><b>🇮🇹 {html.escape(x['it'])}</b><div class='rtl'>🇮🇷 {html.escape(x['fa'])}</div></div>",unsafe_allow_html=True)
        st.subheader("اشتباهات رایج")
        for x in L["mistakes"]:st.error(f"❌ {x['wrong']}  →  ✅ {x['right']}\n\n{x['why']}")
        if st.button("✓ درس را مطالعه کردم"):mark("grammar","lesson studied",5,f"Unit {g['unit']}");st.rerun()

elif page.startswith("📝"):
    keycheck();hero("04 • تمرین گرامر","برای هر Unit همان منوی گرامر؛ ۱۰ سؤال، تصحیح سخت‌گیرانه و نتیجه دائمی.")
    gs=grammar_status();u=st.selectbox("Unit تمرین",range(len(GRAMMAR_A2)),format_func=lambda i:f"{i+1:02d} · {GRAMMAR_A2[i]['title']}")
    g=GRAMMAR_A2[u];kind=f"grammar_ex_{g['unit']}";ex=get_daily(kind)
    if not ex and st.button("ساخت 10 تمرین",type="primary"):
        ex=safe(grammar_exercises,g["title"])
        if ex:put_daily(kind,ex)
    if ex:
        for x in ex:st.markdown(f"**{x['n']}. [{x['type']}]** {x['q']}")
        ans=st.text_area("جواب 1 تا 10",height=230,placeholder="1) ...\n2) ...\n...\n10) ...")
        if st.button("تصحیح سخت‌گیرانه",type="primary") and ans.strip():
            r=safe(grade,g["title"],ex,ans)
            if r:
                save_attempt("grammar",g["unit"],ans,r,int(r["score"]));set_grammar_score(g["unit"],int(r["score"]));mark("exercises","grammar exercises",10,f"Unit {g['unit']} · {r['score']}/10")
                st.metric("نمره",f"{r['score']}/10")
                for q in r["results"]:st.write(("✅" if q["ok"] else "❌"),q["n"],q["answer"],"—",q["why_fa"])
                st.markdown(f"<div class='rtl'>{r['feedback_fa']}</div>",unsafe_allow_html=True)
    hist=[dict(x) for x in attempts("grammar") if x["ref"]==str(g["unit"])]
    if hist:st.dataframe(pd.DataFrame(hist)[["day","score","ts"]],use_container_width=True,hide_index=True)

elif page.startswith("📖"):
    keycheck();hero("05 • متن روز","هر روز یک Reading جدید؛ از A2 ساده شروع می‌شود و به‌تدریج سخت‌تر می‌شود.")
    R=get_daily("reading")
    if not R and st.button("ساخت متن امروز",type="primary"):
        R=safe(reading,course_day())
        if R:put_daily("reading",R);log("reading","daily reading generated",2,R["level"])
    if R:
        st.markdown(f"<div class='card'><span class='step'>{R['level']}</span><h2>{R['title']}</h2><p style='font-size:1.12rem;line-height:2'>{R['text']}</p></div>",unsafe_allow_html=True)
        st.subheader("واژه‌های مهم");st.dataframe(pd.DataFrame(R["words"]),use_container_width=True,hide_index=True)
        with st.expander("خلاصه فارسی"):st.markdown(f"<div class='rtl'>{R['summary_fa']}</div>",unsafe_allow_html=True)
        st.subheader("درک مطلب")
        for i,q in enumerate(R["questions"],1):st.write(i,q["q"])
        if st.button("✓ متن امروز را خواندم"):mark("reading","daily reading completed",10,R["level"]);st.rerun()

elif page.startswith("✍️"):
    keycheck();hero("06 • انشا","موضوع‌ها از روزمره و ساده به بیان نظر و موضوع‌های B1 حرکت می‌کنند.")
    idx=(course_day()-1)%len(WRITING_TOPICS);topic=WRITING_TOPICS[idx]
    st.markdown(f"<div class='card'><span class='step'>TOPIC {idx+1:02d}</span><h3>{topic}</h3></div>",unsafe_allow_html=True)
    text=st.text_area("ایتالیایی بنویس",height=260)
    if st.button("تصحیح سخت‌گیرانه",type="primary") and text.strip():
        r=safe(writing_feedback,topic,text)
        if r:
            save_journal(topic,text,r["corrected"],json.dumps(r,ensure_ascii=False),int(r["score"]));mark("writing","writing corrected",10,f"{r['score']}/10")
            st.metric("نمره",f"{r['score']}/10");st.subheader("نسخه اصلاح‌شده");st.write(r["corrected"])
            for e in r["errors"]:st.error(f"{e['original']} → {e['correct']}\n\n{e['why_fa']}")
            st.markdown(f"<div class='rtl'>{r['feedback_fa']}</div>",unsafe_allow_html=True)

elif page.startswith("🗣️"):
    keycheck();hero("07 • مکالمه","بعد از Reading و Writing: همان زبان را با صدای خودت فعال کن.")
    topic=CONVERSATION_TOPICS[(course_day()-1)%len(CONVERSATION_TOPICS)]
    st.write("موضوع امروز:",f"**{topic}**")
    audio=st.audio_input("🎤 ایتالیایی صحبت کن")
    if audio:
        sig=len(audio.getvalue())
        if st.session_state.get("sig")!=sig:
            st.session_state.sig=sig;tr=safe(transcribe_audio,audio.getvalue())
            if tr:
                r=safe(voice_reply,topic,"",tr)
                if r:
                    spoken=(r["reply"]+" "+r["question"]).strip();save_speaking(topic,tr,spoken);mark("speaking","voice session",5,topic)
                    st.write("**شنیدم:**",tr);st.success(spoken);st.audio(speech_bytes(spoken),format="audio/mp3",autoplay=True)
                    st.info("اصلاح: "+r["correction_fa"]+"\n\nنسخه بهتر: "+r["better"])

elif page.startswith("🎯"):
    hero("08 • مرور روز","چک نهایی قبل از پایان روز.")
    t=today_row();labels=[("واژگان","vocab"),("اصطلاحات","idioms"),("گرامر","grammar"),("تمرین","exercises"),("متن","reading"),("انشا","writing"),("مکالمه","speaking")]
    for l,k in labels:st.write("✅" if t.get(k) else "⬜",l)
    if st.button("ثبت پایان مطالعه امروز",type="primary"):mark("review","daily review completed",10);st.balloons();st.rerun()

elif page.startswith("📅"):
    hero("09 • پیشرفت و تقویم","هیچ نتیجه‌ای با تغییر صفحه از بین نمی‌رود؛ تاریخچه در SQLite نگهداری می‌شود.")
    rows=[dict(x) for x in progress(180)];df=pd.DataFrame(rows)
    if not df.empty:
        df["total"]=df[SECTIONS].sum(axis=1);df["percent"]=(df["total"]/len(SECTIONS)*100).round()
        a,b,c=st.columns(3);a.metric("Streak",f"{streak()} روز");b.metric("روزهای فعال",int((df.total>0).sum()));c.metric("امروز",f"{int(df.iloc[0].percent)}%")
        st.line_chart(df.sort_values("day").set_index("day")["percent"])
        show=df[["day"]+SECTIONS+["percent"]].copy()
        for k in SECTIONS:show[k]=show[k].map({1:"✓",0:"—"})
        st.dataframe(show,use_container_width=True,hide_index=True)
    st.subheader("نتایج گرامر")
    gs=grammar_status()
    data=[{"Unit":g["unit"],"Grammar":g["title"],"Status":gs.get(g["unit"],{}).get("status","not_started"),
    "Best /10":gs.get(g["unit"],{}).get("best_score",0),"Attempts":gs.get(g["unit"],{}).get("attempts",0)} for g in GRAMMAR_A2]
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
