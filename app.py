"""Last Frame: upload a new screenplay, connect your model, explore and refine cuts."""
import hashlib
import html
import json
from pathlib import Path
import streamlit as st
from ai_engine import (Settings,PROVIDERS,ModelError,uploaded_episodes,analyse,
                       decision_for,explain,export_zip,validate_decision,cache_id)
from promo import validate
from sample_data import load_sample

ROOT=Path(__file__).parent
st.set_page_config(page_title='Last Frame | Promo Finder',page_icon='🎬',layout='wide')
st.markdown('<style>'+ (ROOT/'ui.css').read_text() +'</style>',unsafe_allow_html=True)

def clear_session():
    for k in list(st.session_state):del st.session_state[k]

def set_inputs(episodes,fingerprint):
    if st.session_state.get('input_id')!=fingerprint:
        st.session_state.update(episodes=episodes,input_id=fingerprint,cache={},chat=[])
        st.session_state.pop('run',None)
        st.session_state.pop('focus',None)

def settings_or_error():
    try:return Settings(provider,model.strip(),key.strip(),brief,*duration)
    except ValueError as e:st.error(str(e));return None

st.caption('CHOOSE YOUR WORKSPACE')
workspace=st.radio('Workspace',['Sample results · 50 episodes','New analysis'],horizontal=True,key='workspace',label_visibility='collapsed')
is_sample=workspace=='Sample results · 50 episodes'
provider=model=key=brief=''
duration=(20,60)
can_run=False
if is_sample:
    with st.sidebar:
        st.subheader('50-episode sample')
        st.write('Explore the saved results from the assignment story.')
        st.caption('No upload or API key needed. Switch to New analysis to analyse another set of scripts.')
else:
    with st.sidebar:
        st.subheader('Connect your AI')
        provider=st.selectbox('Provider',list(PROVIDERS),key='provider')
        default_model=PROVIDERS[provider][1]
        default_key=PROVIDERS[provider][2] if len(PROVIDERS[provider])>2 else ''
        model=st.text_input('Model ID',value=default_model,key='model_'+provider,
            placeholder='Enter a model available to your API account')
        key_input=st.text_input('API key',value='',type='password',key='api_key_'+provider,
            placeholder='Using pre-configured server key' if default_key else 'Paste your own key')
        key=key_input.strip() or default_key
        st.caption('Your key is used by this app server to contact the selected provider. It is kept in this session, not written to files or downloads. Use only a deployment you trust.')
        if provider.startswith('Google Gemini'):
            st.link_button('Get a Gemini API key','https://aistudio.google.com/apikey')
        st.divider()
        st.subheader('Creative direction')
        duration=st.slider('Promo length (seconds)',20,60,(20,60),key='duration')
        brief=st.text_area('What should the AI prioritize?',placeholder='For example: identity reveals, clear stakes, less graphic violence.',max_chars=2000,key='brief')
        st.caption('20–60 seconds · first-3-second hook · unresolved ending · cold audience. Find/resume reapplies this brief; individual chat refinements apply to the current result.')
        st.button('Clear session and key',on_click=clear_session,use_container_width=True)


st.markdown("""<section class="hero">
<div class="eyebrow">LAST FRAME &nbsp; / &nbsp; AI PROMO FINDER</div>
<h1>Your next great promo<br>is already in your story.</h1>
<p>Turn episode scripts into ranked, ready-to-review promo moments.<br>Find the hook. Keep the cliffhanger. Give your AI editor feedback.</p>
<div class="steps"><span><b>01</b> Upload scripts</span><span><b>02</b> Discover moments</span><span><b>03</b> Refine your cuts</span></div>
</section>""",unsafe_allow_html=True)

if is_sample:
    st.info('SAVED SAMPLE · Results for all 50 assignment episodes. These are saved editorial decisions, not a fresh API analysis. New analysis runs separately on your uploads.')
    run=load_sample(ROOT)
    if run is None:
        st.warning('The confidential 50-episode sample is included in the private submission bundle. This code-only copy does not include it. Choose New analysis to use your own scripts.')
        st.stop()
    episodes=[{'episode':r['episode']} for r in run['result']['coverage']]
else:
    with st.container(border=True,key='upload_panel'):
        st.markdown('<div class="panel-label panel-blue">NEW ANALYSIS / YOUR FILES</div>',unsafe_allow_html=True)
        st.subheader('Analyse another story')
        st.write('Upload a new set of scripts and use your own AI connection. These results stay separate from the saved sample.')
        uploads=st.file_uploader('Upload a show: ZIP or one/more TXT episodes',type=['zip','txt'],accept_multiple_files=True,key='uploads')
        st.caption('Timestamped scripts · Up to 100 episodes · 10 MB total · One show at a time')
        st.download_button('Download an input-format example',(ROOT/'examples/synthetic_episode.txt').read_bytes(),file_name='example_episode.txt',mime='text/plain')
    if uploads:
        files=[(f.name,f.getvalue()) for f in uploads]
        fingerprint=hashlib.sha256(b''.join(name.encode()+hashlib.sha256(data).digest() for name,data in files)).hexdigest()
        try:set_inputs(uploaded_episodes(files),fingerprint)
        except (ValueError,OSError) as e:
            st.error(str(e));st.stop()
    episodes=st.session_state.get('episodes',[])
    if not episodes:
        st.info('Upload scripts to start a new analysis. Your saved 50-episode sample is always available in Sample results.')
        st.stop()
    st.caption(f'{len(episodes)} episodes ready · {sum(len(e["beats"]) for e in episodes):,} timestamped cues')
    with st.expander('Inspect parsed input'):
        st.dataframe([dict(episode=e['episode'],file=e['file'],cues=len(e['beats'])) for e in episodes],hide_index=True,use_container_width=True)
    can_run=bool(key.strip() and model.strip())
    if not can_run:st.caption('Enter your provider, model ID and API key in the sidebar to analyse these scripts.')
    if st.button('Find promos / resume analysis',type='primary',disabled=not can_run,use_container_width=True):
        settings=settings_or_error()
        if settings:
            progress=st.progress(0,text='Starting AI review…')
            with st.spinner('AI is reading your episodes. Valid decisions are kept in this session.'):
                run=analyse(episodes,settings,st.session_state.setdefault('cache',{}),
                    lambda done,total,msg:progress.progress(done/total,text=msg))
            st.session_state['run']=run
            st.session_state['chat']=[]
            st.rerun()
    run=st.session_state.get('run')
    if not run:st.stop()

result=run['result']
if not is_sample and run['audit'].get('settings'):
    used=run['audit']['settings']
    st.caption(f'AI run: {used["provider"]} / {used["model"]} · direction: {used["brief"] or "Default editorial brief"} · {used["min_seconds"]}–{used["max_seconds"]}s')
    if (provider,model.strip(),brief,*duration)!=(used['provider'],used['model'],used['brief'],used['min_seconds'],used['max_seconds']):
        st.warning('Settings have changed. Click Find promos to apply them to your new analysis.')
if not result['complete']:
    st.warning(f'Incomplete run: {len(run["decisions"])}/{len(episodes)} episodes validated. Valid results are cached; fix the reported issue and resume.')
    st.dataframe(result['errors'],hide_index=True,use_container_width=True)

m1,m2,m3=st.columns(3)
with m1:
    with st.container(key='metric_reviewed'):st.metric('Episodes reviewed',f'{len(run["decisions"])}/{len(episodes)}')
with m2:
    with st.container(key='metric_promos'):st.metric('Promos shortlisted',len(result['promos']))
with m3:
    with st.container(key='metric_passes'):st.metric('Explicit passes',sum(r['status']=='pass' for r in run['decisions']))
st.caption('Scores are AI editorial judgments, not predicted views or conversion. All displayed cuts passed code checks. An editor must check narrative truth and actual footage.')

if is_sample:
    tab_short,tab_all=st.tabs(['Ranked shortlist','All episodes & downloads'])
else:
    tab_short,tab_chat,tab_all=st.tabs(['Ranked shortlist','Talk to your AI editor','All episodes & downloads'])
with tab_short:
    query=st.text_input('Search your promos',placeholder='Search episode, hook, or unanswered question')
    promos=[p for p in result['promos'] if query.casefold() in json.dumps(p,ensure_ascii=False).casefold()]
    if not promos:st.info('No promos match. Check the episode decisions or ask the editor to reconsider a passed episode.')
    for p in promos:
        with st.container(border=True,key=f'promo_card_{p["episode"]}'):
            st.markdown(f'<div class="promo-meta"><span class="rank-badge">#{p["rank"]:02d}</span> EPISODE {p["episode"]} &nbsp; · &nbsp; {p["duration_seconds"]:g}s <span class="score-badge">Editorial score {p["score"]:g}/100</span></div>',unsafe_allow_html=True)
            st.subheader(p['open_question'])
            st.code(' + '.join(s['start']+' → '+s['end'] for s in p['segments']),language=None)
            hook_col,cliff_col=st.columns(2)
            with hook_col:
                st.markdown('<div class="quote-box hook"><div class="quote-label">The opening hook</div><p>'+html.escape(p['hook']['text'])+'</p></div>',unsafe_allow_html=True)
            with cliff_col:
                st.markdown('<div class="quote-box cliff"><div class="quote-label">The unresolved ending</div><p>'+html.escape(p['cliffhanger']['text'])+'</p></div>',unsafe_allow_html=True)
            st.write(p['why'])
            st.caption(' · '.join(f'{k.title()} {v}/5' for k,v in p['ratings'].items()))
            for flag in p['flags']:st.warning(flag)
            with st.expander('Verify the source evidence'):
                st.dataframe([dict(cue=b['id'],start=b['start'],end=b['end'],kind=b['kind'],text=b['text']) for b in p['evidence']],hide_index=True,use_container_width=True)

if not is_sample:
    with tab_chat:
        with st.container(key='editor_intro'):
            st.markdown('**Your AI editor, one conversation away.**  \nAsk why a cut works, explore another angle, or reconsider a passed episode. Choose **Refine cut** to apply feedback and revalidate the timestamps.')
        focus=st.selectbox('Episode to discuss',[e['episode'] for e in episodes],format_func=lambda e:f'Episode {e}',key='focus')
        action=st.radio('Editor action',['Explain / ask','Refine cut'],horizontal=True)
        history=st.session_state.setdefault('chat',[])
        for msg in history:
            if msg['episode']==focus:
                with st.chat_message(msg['role']):st.markdown(msg['content'])
        question=st.chat_input('For example: why stop here? / Find a clearer identity-reveal hook.',disabled=not can_run,max_chars=2000)
        if question:
            settings=settings_or_error()
            if settings:
                ep=next(e for e in episodes if e['episode']==focus)
                current=next((r for r in run['decisions'] if r['episode']==focus),None)
                history.append(dict(role='user',content=question,episode=focus))
                try:
                    with st.spinner('Your AI editor is checking the source…'):
                        if action=='Refine cut':
                            row,traces=decision_for(ep,settings,feedback=question,previous=current)
                            if any(r['episode']==focus for r in run['decisions']):
                                run['audit'].setdefault('decision_history',[]).append(current)
                            new_rows=[r for r in run['decisions'] if r['episode']!=focus]+[row]
                            ids={r['episode'] for r in new_rows}
                            new_result=validate([e for e in episodes if e['episode'] in ids],new_rows)
                            remaining=[e for e in result['errors'] if e['episode']!=focus]
                            new_result.update(complete=not remaining and len(ids)==len(episodes),expected_episodes=len(episodes),errors=remaining)
                            run['decisions']=sorted(new_rows,key=lambda r:r['episode']);run['result']=new_result
                            run['raw_responses'].append(dict(episode=focus,action='refine',attempts=traces))
                            run['audit'].setdefault('refinements',[]).append(dict(episode=focus,feedback=question,settings=settings.public()))
                            run['audit'].update(complete=new_result['complete'],validated_decisions=len(new_rows))
                            st.session_state.setdefault('cache',{})[cache_id(ep,settings)]=(row,traces)
                            if run['audit']['kind']=='synthetic_demo':run['audit']['kind']='synthetic_demo_with_live_refinement'
                            answer='Updated and revalidated this episode. '+row['reason']
                        else:
                            answer=explain(ep,current,question,settings,history=[h for h in history[:-1] if h['episode']==focus])
                    history.append(dict(role='assistant',content=answer,episode=focus))
                except (ModelError,ValueError) as e:
                    history.append(dict(role='assistant',content=str(e)+' Previous cuts are unchanged.',episode=focus))
                st.rerun()

with tab_all:
    with st.container(key='download_intro'):
        st.markdown('**From shortlist to editor handoff.**  \nReview every episode decision, then download your cut list, source evidence and AI outputs in one ZIP.')
    st.dataframe(result['coverage'],hide_index=True,use_container_width=True)
    st.download_button('Download run · JSON + CSV + HTML + AI responses',export_zip(run),file_name='sample-50-episode-results.zip' if is_sample else 'new-analysis-results.zip',mime='application/zip',use_container_width=True)
    st.caption('Downloads contain story excerpts. Share with the content owner/recruiter; do not publish confidential runs. The app does not save uploads, keys or results to disk.')
    with st.expander('Run provenance'):
        st.json(run['audit'])
