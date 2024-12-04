import flet as ft
import requests
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

#データベース初期化用SQL
INIT_DATABASE_SQL = """
CREATE TABLE IF NOT EXISTS areas (
    area_code TEXT PRIMARY KEY,
    area_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_code TEXT NOT NULL,
    forecast_date TEXT NOT NULL,
    weather_condition TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (area_code) REFERENCES areas (area_code),
    UNIQUE(area_code, forecast_date)
);

CREATE TABLE IF NOT EXISTS temperatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_id INTEGER NOT NULL,
    temperature TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (forecast_id) REFERENCES weather_forecasts (id)
);

CREATE TABLE IF NOT EXISTS rain_probabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_id INTEGER NOT NULL,
    probability TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (forecast_id) REFERENCES weather_forecasts (id)
);

CREATE TABLE IF NOT EXISTS wind_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_id INTEGER NOT NULL,
    wind_detail TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (forecast_id) REFERENCES weather_forecasts (id)
);
"""

class WeatherDatabase:
    def __init__(self, db_path: str = "weather.db"):
        self.db_path = db_path
        self.initialize_database()
    
    def initialize_database(self) -> None:
        """データベースの初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executescript(INIT_DATABASE_SQL)
                conn.commit()
        except sqlite3.Error as e:
            print(f"データベース初期化エラー: {e}")
            raise

    def save_area_data(self, area_code: str, area_name: str) -> None:
        """エリア情報の保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute(
                    "INSERT OR REPLACE INTO areas (area_code, area_name, created_at) VALUES (?, ?, ?)",
                    (area_code, area_name, now)
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"エリア情報保存エラー: {e}")
            raise

    def save_weather_data(self, area_code: str, weather_data: Dict) -> None:
        """天気予報データの保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                #天気予報基本情報の保存
                cursor.execute(
                    """INSERT OR REPLACE INTO weather_forecasts 
                       (area_code, forecast_date, weather_condition, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (area_code, 
                     weather_data["datetime"], 
                     weather_data["weather"], 
                     now)
                )
                
                forecast_id = cursor.lastrowid
                
                #気温情報の保存
                if weather_data.get("temp"):
                    cursor.execute(
                        """INSERT INTO temperatures 
                           (forecast_id, temperature, created_at)
                           VALUES (?, ?, ?)""",
                        (forecast_id, weather_data["temp"], now)
                    )
                
                #降水確率の保存
                if weather_data.get("rain_prob"):
                    cursor.execute(
                        """INSERT INTO rain_probabilities 
                           (forecast_id, probability, created_at)
                           VALUES (?, ?, ?)""",
                        (forecast_id, weather_data["rain_prob"], now)
                    )
                
                #風情報の保存
                if weather_data.get("wind"):
                    cursor.execute(
                        """INSERT INTO wind_conditions 
                           (forecast_id, wind_detail, created_at)
                           VALUES (?, ?, ?)""",
                        (forecast_id, weather_data["wind"], now)
                    )
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"天気データ保存エラー: {e}")
            raise

    def get_weather_data(self, area_code: str, target_date: str = None) -> List[Dict]:
        """
        天気データを取得する
        
        Args:
            area_code: 地域コード
            target_date: 対象日付（YYYY-MM-DD形式）
        
        Returns:
            List[Dict]: 天気データのリスト
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    weather_forecasts.forecast_date,
                    weather_forecasts.weather_condition,
                    temperatures.temperature,
                    rain_probabilities.probability,
                    wind_conditions.wind_detail
                FROM weather_forecasts
                LEFT JOIN temperatures ON weather_forecasts.id = temperatures.forecast_id
                LEFT JOIN rain_probabilities ON weather_forecasts.id = rain_probabilities.forecast_id
                LEFT JOIN wind_conditions ON weather_forecasts.id = wind_conditions.forecast_id
                WHERE weather_forecasts.area_code = ?
                """
                
                params = [area_code]
                if target_date:
                    #日付の比較条件を修正
                    query += " AND date(substr(weather_forecasts.forecast_date, 1, 10)) = date(?)"
                    params.append(target_date)
                
                #結果を日時でソート
                query += " ORDER BY weather_forecasts.forecast_date"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                weather_data = []
                for row in results:
                    weather_data.append({
                        "datetime": row[0],
                        "weather": row[1],
                        "temp": row[2] or "--",
                        "rain_prob": row[3] or "--",
                        "wind": row[4] or "--"
                    })
                
                return weather_data
        except sqlite3.Error as e:
            print(f"天気データ取得エラー: {e}")
            raise

def main(page: ft.Page):
    #基本的なウィンドウ設定
    page.window.width = 1920
    page.window.height = 1080
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#1a1a2e"
    page.scroll = "always"
    
    #モダンなカラーパレット定義
    COLORS = {
        "primary": "#0f3460",
        "secondary": "#16213e",
        "accent": "#e94560",
        "background": "#1a1a2e",
        "surface": "#162447",
        "text_primary": "#ffffff",
        "text_secondary": "#b2b2b2",
        "border": "#2a2a4a"
    }

    #データベースインスタンスの作成
    db = WeatherDatabase()

    #UI部品の定義
    sidebar = ft.Container(
        width=300,
        height=page.window.height,
        bgcolor=COLORS["secondary"],
        padding=ft.padding.all(20),
        border=ft.border.only(right=ft.BorderSide(1, COLORS["border"]))
    )

    area_dropdown = ft.Dropdown(
        width=260,
        height=60,
        label="地域を選択",
        label_style=ft.TextStyle(
            size=18, 
            weight=ft.FontWeight.W_500,
            color=COLORS["text_primary"]
        ),
        border_radius=12,
        bgcolor=COLORS["surface"],
        focused_border_color=COLORS["accent"],
        color=COLORS["text_primary"],
        border_color=COLORS["border"],
    )

    date_picker = ft.DatePicker()
    date_picker_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.CALENDAR_TODAY),
                    ft.Text("日付を選択", size=18, color=COLORS["text_primary"])
                ]
            ),
            style=ft.ButtonStyle(
                bgcolor=COLORS["surface"],
                color=COLORS["text_primary"]
            ),
            on_click=lambda _: date_picker.pick_date(),
        ),
        width=260,
        height=60,
    )

    weather_grid = ft.GridView(
        expand=True,
        max_extent=400,
        child_aspect_ratio=0.9,
        spacing=30,
        run_spacing=30,
        padding=40,
    )

    #天気アイコンマッピング
    WEATHER_ICONS = {
        "晴れ": "☀️",
        "くもり": "☁️",
        "雨": "🌧️",
        "雪": "🌨️",
        "雷": "⚡",
        "みぞれ": "🌨️",
    }

    def get_weather_icon(weather: str) -> str:
        """天気文字列からアイコンを取得"""
        weather_patterns = weather.split("後")
        if len(weather_patterns) > 1:
            weather = weather_patterns[1]
        elif "のち" in weather:
            weather = weather.split("のち")[1]
            
        for key in WEATHER_ICONS:
            if key in weather:
                return WEATHER_ICONS[key]
        return "🌈"

    def create_weather_card(date: str = "", weather: str = "", temp: str = "", 
                            rain_prob: str = "", wind: str = "") -> ft.Card:
            """天気情報カードを生成"""
            return ft.Card(
                elevation=0,
                content=ft.Container(
                    padding=35,
                    content=ft.Column(
                        controls=[
                            #日付表示部分
                            ft.Container(
                                content=ft.Text(
                                    date,
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLORS["text_primary"]
                                ),
                                margin=ft.margin.only(bottom=25)
                            ),
                            #天気アイコンと天気表示部分
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        get_weather_icon(weather),
                                        size=50,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            weather,
                                            size=20,
                                            color=COLORS["text_primary"],
                                            weight=ft.FontWeight.W_500,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        width=300,
                                        margin=ft.margin.only(top=10)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                margin=ft.margin.only(bottom=25)
                            ),
                            #詳細情報表示部分
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.icons.THERMOSTAT, 
                                                        color=COLORS["accent"],
                                                        size=24),
                                                    ft.Text(f"{temp}℃", 
                                                        size=20,
                                                        color=COLORS["text_primary"])
                                                ],
                                                spacing=10
                                            ),
                                            margin=ft.margin.only(bottom=15)
                                        ),
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.icons.WATER_DROP, 
                                                        color=COLORS["accent"],
                                                        size=24),
                                                    ft.Text(f"{rain_prob}%", 
                                                        size=20,
                                                        color=COLORS["text_primary"])
                                                ],
                                                spacing=10
                                            ),
                                            margin=ft.margin.only(bottom=15)
                                        ),
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.icons.AIR, 
                                                        color=COLORS["accent"],
                                                        size=24),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            wind, 
                                                            size=20,
                                                            color=COLORS["text_primary"]
                                                        ),
                                                        width=200,
                                                    )
                                                ],
                                                spacing=10
                                            )
                                        )
                                    ],
                                    spacing=5
                                ),
                                bgcolor=COLORS["surface"],
                                padding=25,
                                border_radius=15
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=COLORS["secondary"],
                    border_radius=20,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[
                            COLORS["secondary"],
                            ft.colors.with_opacity(0.8, COLORS["surface"])
                        ]
                    )
                )
            )

    def format_datetime(date_str: str) -> str:
        """日時フォーマットを整形"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            weekday = ['月','火','水','木','金','土','日'][dt.weekday()]
            return f"{dt.strftime('%-m/%-d')}({weekday})"
        except:
            return date_str

    def get_area_list() -> None:
        """地域リストを取得してDBに保存"""
        try:
            response = requests.get(
                "https://www.jma.go.jp/bosai/common/const/area.json",
                timeout=10
            )
            response.raise_for_status()
            areas = response.json()
            
            options = []
            offices = areas.get("offices", {})
            
            for code, info in sorted(offices.items(), key=lambda x: x[1].get("name", "")):
                if len(code) == 6:
                    name = info.get("name", "")
                    if name:
                        #DBに保存
                        db.save_area_data(code, name)
                        options.append(ft.dropdown.Option(key=code, text=name))
            
            area_dropdown.options = options
            page.update()
            
        except Exception as e:
            show_error_dialog(f"地域情報の取得に失敗しました: {str(e)}")

    def show_error_dialog(error_message: str) -> None:
        """エラーダイアログを表示"""
        def close_dlg(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("エラー", size=22, color=COLORS["accent"]),
            content=ft.Text(error_message, 
                          size=18, 
                          color=COLORS["text_primary"]),
            actions=[
                ft.TextButton(
                    "閉じる",
                    on_click=close_dlg,
                    style=ft.ButtonStyle(
                        color=COLORS["accent"]
                    )
                )
            ],
            bgcolor=COLORS["surface"]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def safe_get(data: Dict[str, Any], *keys: str, default: Any = "--") -> Any:
        """安全なデータ取得"""
        for key in keys:
            try:
                data = data[key]
            except (KeyError, IndexError, TypeError):
                return default
        return data

    def get_weather(e) -> None:
        """天気情報を取得してDBに保存し表示"""
        try:
            selected_code = area_dropdown.value
            if not selected_code:
                return

            #ローディング表示
            progress = ft.ProgressRing(
                width=40,
                height=40,
                stroke_width=3,
                color=COLORS["accent"]
            )
            page.add(progress)
            page.update()

            #APIから最新の天気予報を取得
            forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{selected_code}.json"
            response = requests.get(forecast_url, timeout=10)
            response.raise_for_status()
            api_data = response.json()

            if not api_data:
                raise ValueError("天気データが取得できませんでした")

            #天気予報データの解析とDB保存
            weather_data_list = []
            for area_data in api_data:
                time_series = safe_get(area_data, "timeSeries", default=[])
                if not time_series:
                    continue

                weather_series = time_series[0]
                times = safe_get(weather_series, "timeDefines", default=[])
                areas = safe_get(weather_series, "areas", default=[])

                if not areas:
                    continue

                area = areas[0]
                for i, time in enumerate(times):
                    weather_info = {
                        "datetime": time,
                        "weather": safe_get(area, "weathers", i, default="--"),
                        "wind": safe_get(area, "winds", i, default="--"),
                        "temp": "--",
                        "rain_prob": "--"
                    }

                    if len(time_series) > 2:
                        temp_areas = safe_get(time_series[2], "areas", default=[])
                        if temp_areas:
                            weather_info["temp"] = safe_get(temp_areas[0], "temps", i, default="--")

                    if len(time_series) > 1:
                        rain_areas = safe_get(time_series[1], "areas", default=[])
                        if rain_areas:
                            weather_info["rain_prob"] = safe_get(rain_areas[0], "pops", i, default="--")

                    #DBに保存
                    db.save_weather_data(selected_code, weather_info)
                    weather_data_list.append(weather_info)

            #選択された日付がある場合はその日のデータのみを取得
            if date_picker.value:
                weather_data_list = db.get_weather_data(
                    selected_code,
                    target_date=date_picker.value
                )

            #天気予報カードの表示
            weather_grid.controls.clear()
            for weather_info in weather_data_list:
                card = create_weather_card(
                    date=format_datetime(weather_info["datetime"]),
                    weather=weather_info["weather"],
                    temp=weather_info["temp"],
                    rain_prob=weather_info["rain_prob"],
                    wind=weather_info["wind"]
                )
                weather_grid.controls.append(card)

            #ローディング表示を削除
            page.controls.remove(progress)
            page.update()

        except Exception as e:
            show_error_dialog(f"天気情報の取得に失敗しました: {str(e)}")

    #ドロップダウンと日付選択の変更イベントを設定
    area_dropdown.on_change = get_weather
    date_picker.on_change = get_weather

    #サイドバーのレイアウト構築
    sidebar.content = ft.Column(
        controls=[
            ft.Container(
                content=ft.Image(
                    src="https://www.jma.go.jp/bosai/common/img/logo.svg",
                    width=100,
                    height=100,
                    fit=ft.ImageFit.CONTAIN,
                    color=COLORS["text_primary"]
                ),
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=30)
            ),
            area_dropdown,
            ft.Container(
                content=date_picker_button,
                margin=ft.margin.only(top=20)
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    page.overlay.append(date_picker)

    #メインレイアウトの構築
    page.add(
        ft.Row(
            controls=[
                sidebar,
                ft.Container(
                    content=weather_grid,
                    expand=True
                )
            ],
            expand=True
        )
    )

    #初期表示時に地域リストを取得
    get_area_list()

if __name__ == "__main__":
    ft.app(target=main)