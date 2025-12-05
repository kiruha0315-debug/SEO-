import streamlit as st
import google.generativeai as genai
import os
import json
import re

# --- 1. 初期設定とAPIキーの取得 ---

st.set_page_config(page_title="SEOコンテンツスタジオ", layout="wide")

st.title("💡 SEO記事骨子生成AI (by Gemini)")
st.markdown("ターゲットキーワードと意図を入力するだけで、検索上位を狙うための**完璧な記事構成（H1, H2, H3）**を自動で生成します。")

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
        st.error("⚠️ APIキーが設定されていません。Streamlit Secretsを確認してください。")

except Exception as e:
    api_key_valid = False
    st.error(f"API設定エラー: {e}")

# --- 2. ユーザー入力フォーム ---

st.subheader("ステップ1: ターゲット情報を入力")

keyword = st.text_input(
    "🔑 メインキーワードを入力してください（例: 初心者向け アフィリエイト 始め方）",
    value="初心者向け アフィリエイト 始め方"
)

intent_options = [
    "ステップバイステップで、今日から始められる具体的な手順を知りたい",
    "アフィリエイトで失敗しないための注意点やリスクを知りたい",
    "収益を最大化するための具体的な戦略（SEO、SNS活用）を知りたい"
]

intent = st.selectbox(
    "🎯 ユーザーの検索意図を選択してください（記事の方向性を決定します）",
    options=intent_options
)

num_h2 = st.slider("🔢 生成する主要セクション（H2）の数", min_value=5, max_value=10, value=7)

st.markdown("---")

# --- 3. 骨子生成ロジック ---

if st.button("🚀 SEO骨子を生成する"):
    if not api_key_valid:
        st.error("APIキーが設定されていないため、処理を実行できません。")
        st.stop()
    if not keyword:
        st.error("メインキーワードを入力してください。")
        st.stop()
    
    # --- システムプロンプトの定義 ---
    # プロのSEOライターとして振る舞うよう指示
    system_prompt = f"""
    あなたはプロのSEOコンテンツストラテジストであり、人気ブログの編集長です。
    ユーザーが指定したキーワードと検索意図に基づき、SEOで上位表示を目指すための、論理的で網羅性の高い記事の骨子（アウトライン）をJSON形式で生成してください。

    **【キーワードと意図】**
    - ターゲットキーワード: 「{keyword}」
    - 検索意図: 「{intent}」

    **【SEOコンテンツ生成ルール】**
    1. **H1タイトル**: 検索意図を完全に満たし、クリック率（CTR）を高める魅力的なタイトルを生成してください。キーワードを自然に含めること。
    2. **H2見出し**: 記事の主要なステップやセクションを{num_h2}個定義し、必ずキーワードの関連語（例: 'アフィリエイトとは' '初期費用' '失敗しない方法'）を含めてください。
    3. **H3見出し**: H2をサポートする詳細な内容（具体的な手順や注意点）を記述し、読者の疑問を完全に解消できるように設計してください。
    4. **網羅性**: 初心者が知りたい「初期設定」「ASP登録」「ブログ開設」「収益化のコツ」など、関連する必須トピックを全て含めてください。
    5. **出力形式**: 以下のJSONスキーマに**厳密に従って**ください。余計な説明や前置きは一切含めないでください。

    {{
      "article_title_H1": "生成されたH1タイトル",
      "outline": [
        {{
          "heading_H2": "H2見出し 1：メインテーマ",
          "sections_H3": [
            "H3見出し 1-1：詳細な手順や具体例",
            "H3見出し 1-2：次のステップ",
          ]
        }},
        // ... (H2セクションは計{num_h2}個生成する)
      ]
    }}
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        with st.spinner("🧠 検索意図と競合を分析し、最適な骨子を設計中..."):
            response = model.generate_content(
                system_prompt, 
                generation_config={"response_mime_type": "application/json"} 
            )

            quiz_data = response.text
            
            # JSONをパースし、セッションステートに保存
            match = re.search(r'\{.*\}', quiz_data, re.DOTALL)
            if match:
                json_string = match.group(0)
                st.session_state.outline_data = json.loads(json_string)
            else:
                st.error("AIからのレスポンスがJSON形式ではありませんでした。")
                st.text(quiz_data)
                st.session_state.outline_data = None
            
    except Exception as e:
        st.error(f"骨子生成中にエラーが発生しました: {e}")
        st.session_state.outline_data = None


# --- 4. 結果表示エリア ---

if 'outline_data' in st.session_state and st.session_state.outline_data:
    data = st.session_state.outline_data
    
    st.markdown("---")
    st.header("✅ 生成された記事骨子 (SEOアウトライン)")

    # H1タイトル
    st.subheader("🥇 H1タイトル (記事の顔)")
    st.code(data.get("article_title_H1", "タイトル生成エラー"), language='markdown')
    
    st.markdown("### 📝 記事構成案 (H2とH3)")

    # H2とH3の構造化表示
    for i, h2_section in enumerate(data.get("outline", [])):
        h2_title = h2_section.get("heading_H2", f"[H2見出し {i+1}]")
        st.markdown(f"**--- 第{i+1}章 ---**")
        st.markdown(f"## {h2_title}")
        
        sections_h3 = h2_section.get("sections_H3", [])
        
        if sections_h3:
            for j, h3_title in enumerate(sections_h3):
                st.markdown(f"#### {h3_title}")
                # H3の下に、後で本文を書くためのプレースホルダーを配置
                st.markdown(f"> *ここに具体的な手順や内容（本文）が入ります。*")
        else:
             st.markdown("#### *（H3見出しが生成されていません。手動で追加してください。）*")

        st.markdown("") # スペース

    st.markdown("---")
    st.info("この骨子に基づき、次のステップでは「記事本文の自動生成」機能を追加していきます。")

# --- 5. 記事本文生成エリア ---

if 'outline_data' in st.session_state and st.session_state.outline_data:
    st.markdown("---")
    st.subheader("ステップ2: 記事本文を生成")
    st.info("⚠️ 本文生成はAIリソースを多く消費するため、時間がかかります。")

    # 新しいボタンの追加
    if st.button("📝 この骨子で記事本文（約2000字）を生成する", key="generate_body_btn"):
        # 骨子データをJSON形式の文字列として取得し、プロンプトに組み込む
        outline_text = json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)

        # --- システムプロンプトの定義（ライティングモード） ---
        body_prompt = f"""
        あなたはプロのSEOライターです。
        以下の「記事骨子（アウトライン）」のJSONデータに**厳密に従い**、SEOに最適化された記事の本文を生成してください。

        【ライティングルール】
        1. **文字数**: 記事全体の目安として、合計で**約2000字**になるように記述してください。
        2. **H2/H3**: 見出しタグ（H2, H3）は**絶対に出力せず**、その下に入る**本文のみ**を記述してください。
        3. **具体性**: 各H3のセクションは、具体的な手順、数値、例、専門用語の解説などを含め、**読者の疑問を完全に解消する**ように記述してください。
        4. **SEO**: ターゲットキーワード（アフィリエイト 始め方）を、本文中に自然な形で複数回含めてください。
        5. **出力形式**: HTMLやMarkdownの装飾は使わず、**プレーンテキスト**として、見出しと本文が連続した形式で出力してください。

        【記事骨子（アウトライン）】
        {outline_text}
        
        【出力開始】
        ---
        """
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash") # 引き続き高速モデルを使用
            
            with st.spinner("✍️ 骨子に基づき、SEOに最適化された記事本文を執筆中..."):
                response = model.generate_content(body_prompt)
                
                # 結果をセッションステートに保存
                st.session_state.article_body = response.text
                st.success("✅ 記事本文の生成が完了しました！")
                
        except Exception as e:
            st.error(f"記事本文の生成中にエラーが発生しました: {e}")
            st.session_state.article_body = None

# --- 6. 生成された記事本文の表示 ---

if 'article_body' in st.session_state and st.session_state.article_body:
    st.markdown("---")
    st.header("最終記事本文（コピペ用）")
    
    # ユーザーがコピーしやすいように st.text_area で表示
    st.text_area(
        "📝 ブログに貼り付け可能な本文", 
        st.session_state.article_body, 
        height=500
    )
    
    st.markdown("---")
    st.success("これで、検索意図を満たし、SEOに最適化された記事のドラフトが完成しました！")
