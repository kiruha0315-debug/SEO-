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
        # 環境設定が完了しているため、エラーではなく注意メッセージに変更
        st.warning("⚠️ APIキーが設定されていません。Streamlit Secretsを確認してください。")

except Exception as e:
    api_key_valid = False
    st.error(f"API設定エラー: {e}")

# セッションステートの初期化
if 'outline_data' not in st.session_state:
    st.session_state.outline_data = None
if 'article_body' not in st.session_state:
    st.session_state.article_body = None
if 'meta_data' not in st.session_state:
    st.session_state.meta_data = None
if 'seo_check' not in st.session_state:
    st.session_state.seo_check = None


# --- 2. ユーザー入力フォーム ---

st.subheader("ステップ1: ターゲット情報を入力")

keyword = st.text_input(
    "🔑 メインキーワードを入力してください（例: 初心者向け アフィリエイト 始め方）",
    value="初心者向け アフィリエイト 始め方",
    key="input_keyword"
)

intent_options = [
    "ステップバイステップで、今日から始められる具体的な手順を知りたい",
    "アフィリエイトで失敗しないための注意点やリスクを知りたい",
    "収益を最大化するための具体的な戦略（SEO、SNS活用）を知りたい"
]

intent = st.selectbox(
    "🎯 ユーザーの検索意図を選択してください（記事の方向性を決定します）",
    options=intent_options,
    key="input_intent"
)

num_h2 = st.slider("🔢 生成する主要セクション（H2）の数", min_value=5, max_value=10, value=7)

st.markdown("---")


# --- 3. 骨子生成ロジック (関数化) ---

def generate_outline(keyword, intent, num_h2):
    """SEO骨子を生成し、セッションステートに保存する"""
    if not api_key_valid:
        st.error("APIキーが設定されていないため、処理を実行できません。")
        return
    if not keyword:
        st.error("メインキーワードを入力してください。")
        return

    system_prompt = f"""
    あなたはプロのSEOコンテンツストラテジストであり、人気ブログの編集長です。
    ユーザーが指定したキーワードと検索意図に基づき、SEOで上位表示を目指すための、論理的で網羅性の高い記事の骨子（アウトライン）をJSON形式で生成してください。
    ... (プロンプトは簡略化しています。詳細は前回のコードを参照) ...
    """
    
    # 既存の骨子生成ロジック（JSON出力）をここに入れる (ここでは省略)
    # ...
    
    # 以前のコードのまま、JSON形式で骨子を生成し、st.session_state.outline_data に保存する処理を続けます
    # ...
    
    # 【注意】元の骨子生成ロジックをここに挿入してください。
    # APIコールとJSONパースの結果が st.session_state.outline_data に入ることが前提です。
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        with st.spinner("🧠 検索意図と競合を分析し、最適な骨子を設計中..."):
            response = model.generate_content(
                system_prompt, 
                generation_config={"response_mime_type": "application/json"} 
            )

            # JSONパース処理
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                json_string = match.group(0)
                st.session_state.outline_data = json.loads(json_string)
                st.session_state.article_body = None # 新しい生成開始で本文をクリア
                st.session_state.meta_data = None
                st.session_state.seo_check = None
                st.success("✅ 記事の骨子（アウトライン）が正常に生成されました。")
            else:
                st.error("AIからの骨子レスポンスがJSON形式ではありませんでした。")
                st.session_state.outline_data = None
                
    except Exception as e:
        st.error(f"骨子生成中にエラーが発生しました: {e}")
        st.session_state.outline_data = None


if st.button("🚀 ステップ1: SEO骨子を生成する"):
    generate_outline(keyword, intent, num_h2)


# --- 4. 骨子の表示 (省略) ---

if st.session_state.outline_data:
    data = st.session_state.outline_data
    # ... (既存の骨子表示コード - H1, H2, H3の表示) ...
    
    st.markdown("---")
    st.header("✅ 生成された記事骨子 (SEOアウトライン)")
    st.subheader("🥇 H1タイトル (記事の顔)")
    st.code(data.get("article_title_H1", "タイトル生成エラー"), language='markdown')
    
    st.markdown("### 📝 記事構成案 (H2とH3)")
    for i, h2_section in enumerate(data.get("outline", [])):
        h2_title = h2_section.get("heading_H2", f"[H2見出し {i+1}]")
        st.markdown(f"**--- 第{i+1}章 ---**")
        st.markdown(f"## {h2_title}")
        sections_h3 = h2_section.get("sections_H3", [])
        if sections_h3:
            for h3_title in sections_h3:
                st.markdown(f"#### {h3_title}")
                st.markdown(f"> *ここに具体的な手順や内容（本文）が入ります。*")
        st.markdown("")


# --- 5. 記事本文生成ロジック ---

def generate_body():
    """記事本文を生成し、セッションステートに保存する"""
    if not st.session_state.outline_data:
        st.error("先に骨子を生成してください。")
        return

    # 骨子データをJSON形式の文字列として取得
    outline_text = json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)
    
    body_prompt = f"""
    あなたはプロのSEOライターです。以下の骨子に厳密に従い、SEOに最適化された記事の本文を生成してください。
    【ライティングルール】1. **合計約2000字**になるように記述。 2. H2/H3タグは**出力せず**、本文のみ記述。 3. 具体的な手順や例を含める。
    【記事骨子】{outline_text}
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        with st.spinner("✍️ 骨子に基づき、SEOに最適化された記事本文を執筆中..."):
            response = model.generate_content(body_prompt)
            st.session_state.article_body = response.text
            st.session_state.meta_data = None
            st.session_state.seo_check = None
            st.success("✅ 記事本文の生成が完了しました！")
            
    except Exception as e:
        st.error(f"記事本文の生成中にエラーが発生しました: {e}")
        st.session_state.article_body = None


if st.session_state.outline_data:
    st.markdown("---")
    st.subheader("ステップ2: 記事本文を生成")
    if st.button("📝 この骨子で記事本文（約2000字）を生成する", key="generate_body_btn"):
        generate_body()


# --- 新機能A: メタ情報生成ロジック ---

def generate_meta(article_body):
    """SEOメタ情報（タイトル、ディスクリプション）を生成する"""
    if not article_body: return
    
    meta_prompt = f"""
    あなたは広告コピーライターであり、SEOスペシャリストです。
    以下の記事本文の内容に基づき、検索結果のクリック率（CTR）を最大化するためのSEOメタ情報をJSON形式で生成してください。

    【ルール】
    1. **meta_title**: 検索結果に表示されるタイトル。**30文字〜35文字**に収め、読者の注意を引く強力なキャッチーなフレーズを使用すること。
    2. **meta_description**: 検索結果に表示される概要文。**100文字〜120文字**に収め、記事の内容を具体的に示し、クリックを促すこと。
    
    【記事本文抜粋】
    {article_body[:2000]}
    
    【出力形式】
    {{
      "meta_title": "生成されたSEOタイトル",
      "meta_description": "生成されたメタディスクリプション"
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        with st.spinner("✨ クリック率を高めるメタ情報を生成中..."):
            response = model.generate_content(meta_prompt, generation_config={"response_mime_type": "application/json"})
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                st.session_state.meta_data = json.loads(match.group(0))
                st.success("✅ メタ情報の生成が完了しました。")
    except Exception as e:
        st.error(f"メタ情報生成中にエラーが発生しました: {e}")

# --- 新機能B: 記事チェックリストロジック ---

def check_seo(article_body, keyword):
    """生成された記事をSEOチェックリストで評価する"""
    if not article_body: return
    
    check_prompt = f"""
    あなたは厳格なSEO監査官です。
    以下の記事本文とターゲットキーワードに基づき、記事の改善点を指摘するチェックリストをJSON形式で生成してください。

    【ターゲットキーワード】: {keyword}
    【記事本文】: {article_body[:3000]}

    【評価項目】
    以下の4つの項目について、改善の必要性を評価してください。
    
    【出力形式】
    {{
      "seo_checklist": [
        {{
          "item": "網羅性・深さ",
          "evaluation": "記事の内容は、ターゲットキーワードの検索意図に対して十分な深さがあるか？競合が触れているトピックに漏れはないか？",
          "status": "OK" / "要改善",
          "suggestion": "具体的な改善提案文"
        }},
        {{
          "item": "キーワード密度・自然さ",
          "evaluation": "ターゲットキーワードは、不自然でなく、過剰でなく、適切に本文に散りばめられているか？",
          "status": "OK" / "要改善",
          "suggestion": "具体的な改善提案文"
        }},
        {{
          "item": "読了性・わかりやすさ",
          "evaluation": "文章は簡潔で、段落分けが適切で、読者が最後まで読みやすいか？",
          "status": "OK" / "要改善",
          "suggestion": "具体的な改善提案文"
        }},
        {{
          "item": "信頼性・専門性",
          "evaluation": "提示された情報に誤りはないか？専門用語の使い方は適切か？",
          "status": "OK" / "要改善",
          "suggestion": "具体的な改善提案文"
        }}
      ]
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        with st.spinner("🔍 記事のSEO監査（チェック）を実行中..."):
            response = model.generate_content(check_prompt, generation_config={"response_mime_type": "application/json"})
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                st.session_state.seo_check = json.loads(match.group(0))
                st.success("✅ SEOチェックが完了しました。")
    except Exception as e:
        st.error(f"SEOチェック中にエラーが発生しました: {e}")


# --- 6. 生成結果の表示と追加処理の実行 ---

if st.session_state.article_body:
    article_body = st.session_state.article_body
    
    st.markdown("---")
    st.header("📝 ステップ3: 最終記事本文とSEOチェック")
    
    # 6-1. メタ情報生成と表示
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✨ メタ情報を生成/チェックする", key="meta_check_btn"):
            generate_meta(article_body)
    with col2:
        if st.button("🔍 SEOチェックリストで評価する", key="check_seo_btn"):
            check_seo(article_body, keyword)
    
    if st.session_state.meta_data:
        st.markdown("#### 📧 メタ情報 (検索結果で表示される部分)")
        meta = st.session_state.meta_data
        st.info(f"**SEOタイトル**: {meta.get('meta_title', 'N/A')} (目安: 30-35文字)")
        st.warning(f"**メタディスクリプション**: {meta.get('meta_description', 'N/A')} (目安: 100-120文字)")

    # 6-2. SEOチェックリストの表示
    if st.session_state.seo_check and st.session_state.seo_check.get("seo_checklist"):
        st.markdown("#### 📋 AIによるSEO改善提案")
        check_list = st.session_state.seo_check["seo_checklist"]
        
        for item in check_list:
            status_icon = "🟢 OK" if item.get('status') == "OK" else "🔴 要改善"
            st.markdown(f"**[{status_icon}] {item.get('item')}**")
            st.markdown(f"> *評価*: {item.get('evaluation')}")
            st.markdown(f"> *提案*: {item.get('suggestion')}")
            st.markdown("---")

    # 6-3. 本文コピペエリア
    st.markdown("### ✍️ 記事本文 (コピペ用)")
    st.text_area(
        "📝 ブログに貼り付け可能な本文", 
        article_body, 
        height=500,
        key="final_body_output"
    )

    # 6-4. 新機能C: ダウンロードボタンの追加
    
    # Markdown形式のファイルコンテンツを作成
    download_content = f"# {data.get('article_title_H1', '記事タイトル')}\n\n"
    if st.session_state.meta_data:
        download_content += f"\n"
        download_content += f"\n\n"
        
    download_content += article_body
    
    st.download_button(
        label="📥 Markdownファイルとしてダウンロード",
        data=download_content.encode('utf-8'),
        file_name=f"seo_article_{keyword.replace(' ', '_')}.md",
        mime="text/markdown"
    )

    st.success("🎉 全てのSEOタスクが完了しました！このファイルをブログに貼り付けてください。")
