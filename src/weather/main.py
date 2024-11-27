import flet as ft
import requests
import json
from datetime import datetime

def main(page: ft.Page):
    #アプリケーションの基本設定
    page.window.width = 1200
    page.window.height = 900
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 40
    page.bgcolor = "#f5f5f5"

    #地域選択用ドロップダウンの設定
    area_dropdown = ft.Dropdown(
        width=400,
        height=55,
        label="地域を選択してください",
        label_style=ft.TextStyle(size=16, color="#666666"),
        border_radius=8,
        bgcolor="#ffffff",
        focused_border_color="#1a73e8",
        focused_bgcolor="#ffffff"
    )

    #天気情報表示用のカード作成
    weather_cards = []
    for _ in range(7):
        card = ft.Card(
            elevation=3,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("", size=24, weight=ft.FontWeight.BOLD, color="#333333"),
                        ft.Text("", size=18, color="#666666"),  #天気
                        ft.Text("", size=18, color="#666666"),  #気温
                        ft.Text("", size=18, color="#666666"),  #降水確率
                        ft.Text("", size=18, color="#666666"),  #風
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor="#ffffff",
                border_radius=12
            ),
            visible=False
        )
        weather_cards.append(card)

    def format_datetime(date_str):
        """日時フォーマットを整形する関数"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            return f"{dt.strftime('%Y年%m月%d日')} {dt.strftime('%H時')}"
        except:
            return date_str

    def get_area_list():
        """地域リストを取得する関数"""
        try:
            response = requests.get(
                "https://www.jma.go.jp/bosai/common/const/area.json",
                timeout=10
            )
            response.raise_for_status()
            areas = response.json()
            
            #都道府県のみを抽出
            options = []
            offices = areas.get("offices", {})
            
            for code, info in sorted(offices.items(), key=lambda x: x[1].get("name", "")):
                if len(code) == 6:  #都道府県コードは6桁
                    name = info.get("name", "")
                    if name:
                        options.append(ft.dropdown.Option(key=code, text=name))
            
            area_dropdown.options = options
            page.update()
            
        except requests.RequestException as e:
            show_error_dialog(f"地域情報の取得に失敗しました: {str(e)}")
        except Exception as e:
            show_error_dialog(f"予期せぬエラーが発生しました: {str(e)}")

    def show_error_dialog(error_message):
        """エラーダイアログを表示する関数"""
        def close_dlg(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("エラー", size=20, color="#d32f2f"),
            content=ft.Text(error_message, size=16),
            actions=[
                ft.TextButton("閉じる", on_click=close_dlg)
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def safe_get(data, *keys, default="--"):
        """安全にデータを取得する関数"""
        for key in keys:
            try:
                data = data[key]
            except (KeyError, IndexError, TypeError):
                return default
        return data

    def get_weather(e):
        """天気情報を取得・表示する関数"""
        try:
            selected_code = area_dropdown.value
            if not selected_code:
                return

            progress = ft.ProgressRing()
            page.add(progress)
            page.update()

            #天気予報データを取得
            forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{selected_code}.json"
            response = requests.get(forecast_url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()

            #データが存在することを確認
            if not weather_data:
                raise ValueError("天気データが取得できませんでした")

            #今日・明日の予報を処理
            today_data = weather_data[0] if weather_data else {}
            time_series = safe_get(today_data, "timeSeries", default=[])

            forecast_info = []

            if time_series:
                #天気情報の取得
                weather_series = time_series[0] if len(time_series) > 0 else {}
                weather_times = safe_get(weather_series, "timeDefines", default=[])
                areas = safe_get(weather_series, "areas", default=[])

                if areas:
                    area = areas[0]
                    for i, time in enumerate(weather_times):
                        weather_info = {
                            "datetime": time,
                            "weather": safe_get(area, "weathers", i, default="--"),
                            "wind": safe_get(area, "winds", i, default="--"),
                        }

                        #降水確率の取得
                        if len(time_series) > 1:
                            pop_areas = safe_get(time_series[1], "areas", default=[])
                            if pop_areas:
                                weather_info["rain_prob"] = safe_get(pop_areas[0], "pops", i, default="--")

                        #気温の取得
                        if len(time_series) > 2:
                            temp_areas = safe_get(time_series[2], "areas", default=[])
                            if temp_areas:
                                weather_info["temp"] = safe_get(temp_areas[0], "temps", i, default="--")

                        forecast_info.append(weather_info)

            #各カードの更新
            for i, card in enumerate(weather_cards):
                if i < len(forecast_info):
                    info = forecast_info[i]
                    controls = card.content.content.controls
                    
                    controls[0].value = format_datetime(info["datetime"])
                    controls[1].value = f"天気: {info['weather']}"
                    controls[2].value = f"気温: {info.get('temp', '--')}℃"
                    controls[3].value = f"降水確率: {info.get('rain_prob', '--')}%"
                    controls[4].value = f"風: {info['wind']}"
                    
                    card.visible = True
                else:
                    card.visible = False

            page.controls.remove(progress)
            page.update()

        except requests.RequestException as e:
            show_error_dialog(f"天気情報の取得に失敗しました: {str(e)}")
        except Exception as e:
            show_error_dialog(f"予期せぬエラーが発生しました: {str(e)}")
            print(f"エラーの詳細: {str(e)}")

    #ドロップダウンの変更イベントを設定
    area_dropdown.on_change = get_weather

    #画面レイアウトの設定
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [ft.Image(
                            src="https://www.jma.go.jp/bosai/common/img/logo.svg",
                            width=120,
                            height=120,
                            fit=ft.ImageFit.CONTAIN,
                        )],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Text(
                        "気象庁天気予報",
                        size=40,
                        weight=ft.FontWeight.BOLD,
                        color="#1a73e8",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    ft.Container(
                        content=area_dropdown,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(height=20),
                    *weather_cards,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=30,
        )
    )

    #初期表示時に地域リストを取得
    get_area_list()

if __name__ == "__main__":
    ft.app(target=main)