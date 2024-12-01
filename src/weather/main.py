import flet as ft
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

def main(page: ft.Page):
    #基本的なウィンドウ設定
    page.window.width = 1400
    page.window.height = 1000
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

    #サイドバーコンテナ
    sidebar = ft.Container(
        width=300,
        height=page.window.height,
        bgcolor=COLORS["secondary"],
        padding=ft.padding.all(20),
        border=ft.border.only(right=ft.BorderSide(1, COLORS["border"]))
    )

    #地域選択ドロップダウン
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

    #天気情報表示用グリッド
    weather_grid = ft.GridView(
        expand=True,
        max_extent=400,  #カードサイズを大きく
        child_aspect_ratio=0.9,  #アスペクト比を調整
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
                padding=35,  #パディングを増加
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
                                    size=50,  #アイコンサイズを大きく
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(  #天気テキスト用の新しいコンテナ
                                    content=ft.Text(
                                        weather,
                                        size=20,
                                        color=COLORS["text_primary"],
                                        weight=ft.FontWeight.W_500,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    width=300,  #幅を固定して折り返し
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
                                    ft.Container(  #風情報用のコンテナを追加
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.icons.AIR, 
                                                       color=COLORS["accent"],
                                                       size=24),
                                                ft.Container(  #風テキスト用のコンテナ
                                                    content=ft.Text(
                                                        wind, 
                                                        size=20,
                                                        color=COLORS["text_primary"]
                                                    ),
                                                    width=200,  #幅を固定
                                                )
                                            ],
                                            spacing=10
                                        )
                                    )
                                ],
                                spacing=5
                            ),
                            bgcolor=COLORS["surface"],
                            padding=25,  #パディングを増加
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
        """地域リストを取得"""
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
        """天気情報を取得して表示"""
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

            #天気予報データを取得
            forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{selected_code}.json"
            response = requests.get(forecast_url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()

            if not weather_data:
                raise ValueError("天気データが取得できませんでした")

            #天気予報データの解析と表示
            weather_grid.controls.clear()
            
            for area_data in weather_data:
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
                        "datetime": format_datetime(time),
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

                    card = create_weather_card(
                        date=weather_info["datetime"],
                        weather=weather_info["weather"],
                        temp=weather_info["temp"],
                        rain_prob=weather_info["rain_prob"],
                        wind=weather_info["wind"]
                    )
                    weather_grid.controls.append(card)

            page.controls.remove(progress)
            page.update()

        except Exception as e:
            show_error_dialog(f"天気情報の取得に失敗しました: {str(e)}")

    #ドロップダウンの変更イベントを設定
    area_dropdown.on_change = get_weather

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
            area_dropdown
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

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