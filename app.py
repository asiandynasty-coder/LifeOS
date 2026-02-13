import streamlit as st
import pandas as pd
import os
import datetime
from dotenv import load_dotenv
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 初期設定
print("🚀 [System] ゲームエンジンの起動...")
load_dotenv()
st.set_page_config(page_title="LifeOS: The Game", page_icon="🎮", layout="centered")

# 2. APIキーチェック (Gemini)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("APIキーが見つかりません。.envを確認してください！")
    st.stop()

# 3. Geminiクライアント
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Gemini接続エラー: {e}")

# --- データベース接続 (Google Sheets) ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SHEET_NAME = "LifeOS_DB" # スプレッドシートの名前

def get_database():
    """スプレッドシートに接続してシートオブジェクトを返す"""
    try:
        # ★修正ポイント: まずローカルにJSONファイルがあるか確認する
        if os.path.exists("service_account.json"):
            # Mac用: フォルダにあるJSONファイルを使う
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPE)
        else:
            # クラウド用: StreamlitのSecretsを使う
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        
        client_gs = gspread.authorize(creds)
        sheet = client_gs.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return None

def load_data():
    """データを読み込む"""
    sheet = get_database()
    if sheet:
        # データがあるか確認してからDataFrame化
        data = sheet.get_all_records()
        if data:
            return pd.DataFrame(data)
    # 空の場合は空のDataFrameを返す
    return pd.DataFrame(columns=["date", "steps", "sleep", "study", "comment", "ai_msg"])

def save_data(date, steps, sleep, study, comment, ai_msg):
    """データを追記する"""
    sheet = get_database()
    if sheet:
        # 新しい行を追加
        new_row = [str(date), steps, sleep, study, comment, ai_msg]
        sheet.append_row(new_row)

# --- AIキャラクター機能 ---
def get_ai_praise(steps, sleep, study, user_comment):
    prompt = f"""
    あなたは「ユーザーの全てを肯定し、褒めちぎるRPGの美少女キャラクター」です。
    ユーザーの今日の活動記録を見て、全力で褒めて、モチベーションを上げてください。
    
    【今日の記録】
    - 歩数: {steps}歩
    - 睡眠: {sleep}時間
    - 作業/勉強: {study}時間
    - ユーザーの一言: {user_comment}

    【条件】
    - 親しみやすく、甘やかす口調で。
    - 数字に触れて具体的に褒める。
    - 150文字以内で、絵文字を多用する。
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"エラー発生！でも君は最高だよ！(Error: {e})"

# --- 画面構築 ---
st.title("🎮 LifeOS: The Game")
st.caption("データは永遠に、Googleスプレッドシートへ。")

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
    with st.spinner("データベースに書き込み中..."):
        ai_response = get_ai_praise(steps, sleep, study, comment)
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # スプレッドシートに保存
        save_data(today, steps, sleep, study, comment, ai_response)
        
        st.success("セーブ完了！データはクラウドに保存されました！")
        st.balloons()
        
        st.subheader("🧚‍♀️ パートナーからのメッセージ")
        st.info(ai_response)

# ステータス画面
st.divider()
st.subheader("📊 現在のステータス (from Google Sheets)")

df = load_data()
if not df.empty:
    # 数値計算のために型変換（エラー防止）
    total_steps = pd.to_numeric(df["steps"], errors='coerce').sum()
    total_study = pd.to_numeric(df["study"], errors='coerce').sum()
    total_logins = len(df)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Lv (継続日数)", f"{total_logins}", delta="+1 day")
    c2.metric("体力 (累計歩数)", f"{int(total_steps):,}", delta=f"+{steps if submitted else 0}")
    c3.metric("知力 (累計時間)", f"{float(total_study):.1f} h", delta=f"+{study if submitted else 0}")
    
    with st.expander("冒険の履歴を見る"):
        st.dataframe(df.sort_index(ascending=False))
else:
    st.info("データがありません。最初の記録をつけてみましょう！")