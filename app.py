import streamlit as st
import pandas as pd
import os
import datetime
from dotenv import load_dotenv
from google import genai

# 1. 初期設定とログ
print("🚀 [System] ゲームエンジンの起動...")
load_dotenv()
st.set_page_config(page_title="LifeOS: The Game", page_icon="🎮", layout="centered")

# 2. APIキーチェック
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("APIキーが見つかりません。.envを確認してください！")
    st.stop()

# 3. Geminiクライアント
try:
    client = genai.Client(api_key=api_key)
    print("✅ [System] Gemini接続OK")
except Exception as e:
    st.error(f"接続エラー: {e}")

# --- データ管理機能 (CSV) ---
CSV_FILE = "activity_log.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=["date", "steps", "sleep", "study", "comment", "ai_msg"])

def save_data(date, steps, sleep, study, comment, ai_msg):
    df = load_data()
    new_data = pd.DataFrame({
        "date": [date],
        "steps": [steps],
        "sleep": [sleep],
        "study": [study],
        "comment": [comment],
        "ai_msg": [ai_msg]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

# --- AIキャラクター機能 ---
def get_ai_praise(steps, sleep, study, user_comment):
    print("🤖 [AI] メッセージ生成中...")
    prompt = f"""
    あなたは「ユーザーの全てを肯定し、褒めちぎるRPGの美少女キャラクター（幼馴染風）」です。
    ユーザーの今日の活動記録を見て、全力で褒めて、モチベーションを上げてください。
    
    【今日の記録】
    - 歩数: {steps}歩 (冒険の距離)
    - 睡眠: {sleep}時間 (HP回復)
    - 作業/勉強: {study}時間 (経験値獲得)
    - ユーザーの一言: {user_comment}

    【条件】
    - 口調は「〜だね！すごい！」「〜だよ！えらい！」と親しみやすく。
    - 数字に触れて具体的に褒める（例：「1万歩も！？伝説級の冒険だね！」）。
    - 150文字以内で、絵文字を多用して元気よく。
    """
    try:
        # 安定版の1.5-flashを使用
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"エラー発生！でも頑張った君はえらい！(Error: {e})"

# --- 画面構築 ---
st.title("🎮 LifeOS: The Game")
st.caption("日々の生活が、冒険になる。")

# 入力フォーム
with st.form("daily_log"):
    col1, col2 = st.columns(2)
    with col1:
        steps = st.number_input("今日の歩数 (歩)", min_value=0, value=5000)
        sleep = st.number_input("睡眠時間 (h)", min_value=0.0, value=7.0, step=0.5)
    with col2:
        study = st.number_input("作業・勉強 (h)", min_value=0.0, value=1.0, step=0.5)
    
    comment = st.text_input("今日の一言日記", placeholder="例：今日はジムに行った！疲れた〜")
    
    submitted = st.form_submit_button("冒険の記録をつける！")

# 結果表示
if submitted:
    with st.spinner("集計中...（AIが褒める準備をしています）"):
        # AI生成
        ai_response = get_ai_praise(steps, sleep, study, comment)
        
        # 保存
        today = datetime.date.today().strftime("%Y-%m-%d")
        save_data(today, steps, sleep, study, comment, ai_response)
        
        # 演出
        st.success("記録完了！経験値を獲得しました！")
        st.balloons()
        
        # メッセージ表示
        st.subheader("🧚‍♀️ パートナーからのメッセージ")
        st.info(ai_response)

# ステータス画面
st.divider()
st.subheader("📊 現在のステータス")

df = load_data()
if not df.empty:
    total_steps = df["steps"].sum()
    total_study = df["study"].sum()
    total_logins = len(df)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Lv (継続日数)", f"{total_logins}", delta="+1 day")
    c2.metric("体力 (累計歩数)", f"{total_steps:,}", delta=f"+{steps if submitted else 0}")
    c3.metric("知力 (累計時間)", f"{total_study:.1f} h", delta=f"+{study if submitted else 0}")
    
    with st.expander("冒険の履歴を見る"):
        st.dataframe(df.sort_index(ascending=False))
else:
    st.info("まだ記録がありません。最初の冒険に出かけましょう！")