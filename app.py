import streamlit as st
import google.generativeai as genai
import os
import json
import re

# --- 1. 初期設定とAPIキーの取得 ---

st.set_page_config(page_title="SEOコンテンツスタジオ (Complete)", layout="wide")

st.title("💡 SEOコンテンツスタジオ：完全版")
st.markdown("キーワード分析、記事生成、SEOチェックまで、すべてをAIが一気通貫で実行します。")

# 🔑 APIキーの取得
try:
    API_KEY = os.environ.get("GEMINI_API_KEY") 
    
    if not API_KEY and 'GEMINI_API_KEY' in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]

    if API_KEY:
        genai.configure(api_key=API_KEY)
        api_key_valid = True
    else:
        api_key_valid = False
        st.warning("⚠️ APIキーが設定されていません。Streamlit Secretsを確認してください。")

except Exception as e:
    api_key_valid = False
    st.error(f"API設定エラー: {e}")

# セッションステートの初期化
if 'outline_data' not in st.session_state:
    st.session_state.outline_data = None
if 'article_body' not in st.session_state:
    st.session_state.article_body = None
if 'revised_body' not in st.session_state:
    st.session_state.revised_body = None
if 'meta_data' not in st.session_state:
    st.session_state.meta_data = None
if 'seo_check' not in st.session_state:
    st.session_state.seo_check = None
if 'is_diagnosis_mode' not in st.session_state:
    st.session_state.is_diagnosis_mode = False


# --- 2. アプリのモード選択 ---

mode = st.radio(
    "アプリのモードを選択してください",
    ('🚀 記事ゼロイチ生成（新規作成）', '🔍 既存コンテンツ診断（添削）'),
    key='app_mode',
    horizontal=True
)
st.markdown("---")

# --- 3. 共通関数定義 ---

def get_gemini_response(prompt, json_mode=False):
    """Gemini APIを呼び出す共通関数"""
    if not api_key_valid:
        st.error("APIキーが設定されていないため、処理を実行できません。")
        return None

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        config = {}
        if json_mode:
            config["response_mime_type"] = "application/json"
        
        response = model.generate_content(prompt, generation_config=config)

        if json_mode:
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return None
        return response.text
    
    except Exception as e:
        st.error(f"AI処理中にエラーが発生しました: {e}")
        return None

def reset_session():
    """セッションステートをリセットする"""
    st.session_state.outline_data = None
    st.session_state.article_body = None
    st.session_state.revised_body = None
    st.session_state.meta_data = None
    st.session_state.seo_check = None
    st.session_state.is_diagnosis_mode = False

# --- 4. メタ情報生成ロジック ---

def generate_meta(article_body):
    """SEOメタ情報（タイトル、ディスクリプション）を生成する"""
    if not article_body: return
    
    meta_prompt = f"""
    あなたは広告コピーライターであり、SEOスペシャリストです。
    以下の記事本文の内容に基づき、検索結果のクリック率（CTR）を最大化するためのSEOメタ情報をJSON形式で生成してください。
    【ルール】1. meta_title: 30文字〜35文字に収め、クリック率を高めること。 2. meta_description: 100文字〜120文字に収め、具体的に示し、クリックを促すこと。
    【記事本文抜粋】{article_body[:2000]}
    【出力形式】 {{"meta_title": "生成されたSEOタイトル", "meta_description": "生成されたメタディスクリプション"}}
    """
    
    with st.spinner("✨ クリック率を高めるメタ情報を生成中..."):
        data = get_gemini_response(meta_prompt, json_mode=True)
        if data:
            st.session_state.meta_data = data
            st.success("✅ メタ情報の生成が完了しました。")

# --- 5. 記事チェックリストロジック ---

def check_seo(article_body, keyword):
    """生成された記事をSEOチェックリストで評価する"""
    if not article_body: return
    
    check_prompt = f"""
    あなたは厳格なSEO監査官です。以下の記事本文とターゲットキーワードに基づき、記事の改善点を指摘するチェックリストをJSON形式で生成してください。
    【ターゲットキーワード】: {keyword}
    【記事本文】: {article_body[:3000]}
    【評価項目】以下の4つの項目について、改善の必要性を評価してください。
    【出力形式】 {{ "seo_checklist": [ {{"item": "網羅性・深さ", "evaluation": "...", "status": "OK" / "要改善", "suggestion": "..."}}, ... ] }}
    """
    
    with st.spinner("🔍 記事のSEO監査（チェック）を実行中..."):
        data = get_gemini_response(check_prompt, json_mode=True)
        if data:
            st.session_state.seo_check = data
            st.success("✅ SEOチェックが完了しました。")

# --- 6. 自動修正ロジック ---

def revise_article(original_body, seo_check_data, keyword):
    """SEOチェックリストの提案に基づき、記事本文を自動修正する"""
    if not original_body or not seo_check_data:
        st.error("記事本文またはSEOチェックデータが不足しています。")
        return

    improvements = []
    for item in seo_check_data.get("seo_checklist", []):
        if item.get("status") == "要改善":
            improvements.append(f"- {item.get('item')}: {item.get('suggestion')}")
    
    if not improvements:
        st.success("🎉 AIによる修正の必要はありません。記事はすでに『OK』レベルです！")
        return

    revision_prompt = f"""
    あなたはプロのSEOライターです。
    以下の「元の記事本文」を、[改善提案リスト]に記載されたすべての指摘を完璧に満たすように修正し、新しい記事本文（修正版）を生成してください。
    【元の記事本文】 {original_body}
    【改善提案リスト】 {'\n'.join(improvements)}
    【ルール】1. 元の記事の構造を保ちながら、本文だけを修正。 2. 修正版の文字数は元の記事と大きく変わらないようにする。 3. プレーンテキスト形式で、修正後の記事本文のみを出力してください。
    """
    
    with st.spinner("🔧 AIが改善提案に基づき、記事本文を自動修正中..."):
        revised_text = get_gemini_response(revision_prompt)
        if revised_text:
            st.session_state.revised_body = revised_text
            st.success("✅ 記事の自動修正が完了しました。修正版をご確認ください。")


# =================================================================
#                         モードごとの表示ロジック
# =================================================================


if mode == '🚀 記事ゼロイチ生成（新規作成）':
    st.session_state.is_diagnosis_mode = False
    
    if st.button("⏪ セッションリセット（最初からやり直す）"):
        reset_session()
        st.rerun()

    # --- 7. 骨子生成ロジック (関数化) ---

    def generate_outline_logic(keyword, intent, num_h2):
        if not api_key_valid: return
        # ... (前述の骨子生成ロジックをここに挿入) ...
        system_prompt = f"""
        あなたはプロのSEOコンテンツストラテジストであり、人気ブログの編集長です。
        ユーザーが指定したキーワードと検索意図に基づき、SEOで上位表示を目指すための、論理的で網羅性の高い記事の骨子（アウトライン）をJSON形式で生成してください。

        **【キーワードと意図】**
        - ターゲットキーワード: 「{keyword}」
        - 検索意図: 「{intent}」

        **【SEOコンテンツ生成ルール】**
        1. **H1タイトル**: 検索意図を完全に満たし、クリック率（CTR）を高める魅力的なタイトルを生成してください。キーワードを自然に含めること。
        2. **H2見出し**: 記事の主要なステップやセクションを{num_h2}個定義し、必ずキーワードの関連語を含めてください。
        3. **H3見出し**: H2をサポートする詳細な内容を記述し、読者の疑問を完全に解消できるように設計してください。
        4. **出力形式**: 以下のJSONスキーマに厳密に従ってください。{{ "article_title_H1": "...", "outline": [ {{ "heading_H2": "...", "sections_H3": [...] }} ] }}
        """

        with st.spinner("🧠 検索意図と競合を分析し、最適な骨子を設計中..."):
            data = get_gemini_response(system_prompt, json_mode=True)
            if data:
                st.session_state.outline_data = data
                st.session_state.article_body = None
                st.session_state.revised_body = None
                st.session_state.meta_data = None
                st.session_state.seo_check = None
                st.success("✅ 記事の骨子（アウトライン）が正常に生成されました。")
    
    # --- UIとボタン配置（新規作成） ---
    
    st.subheader("ステップ1: ターゲット情報を入力")
    keyword = st.text_input("🔑 メインキーワードを入力してください", value="初心者向け アフィリエイト 始め方", key="gen_keyword")
    intent = st.selectbox("🎯 ユーザーの検索意図を選択してください", options=["ステップバイステップで、今日から始められる具体的な手順を知りたい", "失敗しないための注意点を知りたい"], key="gen_intent")
    num_h2 = st.slider("🔢 生成する主要セクション（H2）の数", min_value=5, max_value=10, value=7, key="gen_num_h2")

    if st.button("🚀 ステップ1: SEO骨子を生成する"):
        generate_outline_logic(keyword, intent, num_h2)

    # ... (骨子の表示コード - 変更なし) ...
    if st.session_state.outline_data:
        data = st.session_state.outline_data
        st.markdown("---")
        st.header("✅ 生成された記事骨子")
        st.subheader(f"🥇 H1タイトル: {data.get('article_title_H1', 'タイトルエラー')}")
        
        # 本文生成ロジック
        def generate_body_logic():
            outline_text = json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)
            body_prompt = f"""
            あなたはプロのSEOライターです。以下の骨子に厳密に従い、SEOに最適化された記事の本文を生成してください。
            【ライティングルール】1. **合計約2000字**になるように記述。 2. H2/H3タグは**出力せず**、本文のみ記述。
            【記事骨子】{outline_text}
            """
            with st.spinner("✍️ 記事本文を執筆中..."):
                st.session_state.article_body = get_gemini_response(body_prompt)
                st.success("✅ 記事本文の生成が完了しました！")
                
        if st.button("📝 ステップ2: この骨子で記事本文を生成する", key="gen_body_btn"):
            generate_body_logic()
        
        # ... (H2/H3の表示 - 変更なし) ...
        # (簡略化のため、本文生成後の表示セクションに移ります)


# =================================================================
#                         診断モード
# =================================================================

elif mode == '🔍 既存コンテンツ診断（添削）':
    st.session_state.is_diagnosis_mode = True
    reset_session()
    
    st.header("🔍 既存記事のSEO診断・添削")
    
    diagnosis_keyword = st.text_input(
        "🔑 この記事のターゲットキーワードは何ですか？",
        key="diagnosis_keyword_input"
    )
    existing_article = st.text_area(
        "診断したい記事の本文を貼り付けてください",
        height=500,
        key="existing_article_input"
    )
    
    if st.button("🔬 AIによるSEO診断を開始する"):
        if not existing_article or not diagnosis_keyword:
            st.error("診断には記事本文とターゲットキーワードが必要です。")
        else:
            # 診断モードでは、生成された本文として貼り付けられた本文を使う
            st.session_state.article_body = existing_article
            st.session_state.is_diagnosis_mode = True
            
            # 既存の check_seo 関数を呼び出し、診断を実行
            check_seo(existing_article, diagnosis_keyword)


# =================================================================
#                         共通の結果表示エリア
# =================================================================

current_body = st.session_state.revised_body if st.session_state.revised_body else st.session_state.article_body

if current_body:
    
    target_keyword = st.session_state.get('input_keyword', st.session_state.get('diagnosis_keyword_input', ''))
    
    st.markdown("---")
    st.header("📝 ステップ3: 最終チェックと修正")
    
    # 7. メタ情報生成とチェックリスト実行ボタン
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✨ メタ情報を生成/チェックする", key="meta_check_btn"):
            generate_meta(current_body)
    with col2:
        if st.button("🔍 SEOチェックリストで評価する", key="check_seo_btn"):
            check_seo(current_body, target_keyword)

    # 8. SEOチェックリストの表示
    if st.session_state.seo_check and st.session_state.seo_check.get("seo_checklist"):
        st.markdown("#### 📋 AIによるSEO改善提案")
        check_list = st.session_state.seo_check["seo_checklist"]
        
        is_revised_needed = any(item.get('status') == "要改善" for item in check_list)

        if is_revised_needed:
            st.warning("🔴 要改善の指摘があります。自動修正を試してください。")
            if st.button("🔧 AIによる自動修正を実行する", key="auto_revise_btn"):
                revise_article(current_body, st.session_state.seo_check, target_keyword)
        else:
            st.success("🎉 SEO上の大きな改善点は見つかりませんでした！")

    # 9. メタ情報の表示
    if st.session_state.meta_data:
        st.markdown("#### 📧 メタ情報 (検索結果で表示される部分)")
        meta = st.session_state.meta_data
        st.info(f"**SEOタイトル**: {meta.get('meta_title', 'N/A')} (目安: 30-35文字)")
        st.warning(f"**メタディスクリプション**: {meta.get('meta_description', 'N/A')} (目安: 100-120文字)")
    
    # 10. 本文コピペエリア (修正版優先)
    final_body_to_display = st.session_state.revised_body if st.session_state.revised_body else st.session_state.article_body

    st.markdown("### ✍️ 最終記事本文 (コピペ用)")
    st.text_area(
        "📝 ブログに貼り付け可能な本文", 
        final_body_to_display, 
        height=500,
        key="final_body_output"
    )

    # 11. ダウンロードボタン
    
    # Markdown形式のファイルコンテンツを作成
    download_content = f"## SEOレポート\n\n"
    if st.session_state.meta_data:
        download_content += f"\n"
        download_content += f"\n\n"
    
    download_content += f"# {st.session_state.outline_data.get('article_title_H1') if st.session_state.outline_data else '記事タイトル'}\n\n"
    download_content += final_body_to_display
    
    st.download_button(
        label="📥 Markdownファイルとしてダウンロード",
        data=download_content.encode('utf-8'),
        file_name=f"seo_article_final.md",
        mime="text/markdown"
    )
    
    st.success("🎉 全てのSEOタスクが完了しました！")
