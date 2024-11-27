import flet as ft
import requests
import json

def main(page: ft.Page):
   #画面の基本設定
   page.title = "天気予報アプリ"
   page.window_width = 1000
   page.window_height = 800
   page.theme_mode = ft.ThemeMode.LIGHT
   page.padding = 40
   page.bgcolor = "#f5f5f5"

   #地域選択用ドロップダウン作成
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

   #天気情報表示用カード作成
   weather_card = ft.Card(
       elevation=3,
       content=ft.Container(
           padding=20,
           content=ft.Column(
               controls=[
                   ft.Text("", size=24, weight=ft.FontWeight.BOLD, color="#333333", text_align=ft.TextAlign.CENTER),
               ],
               horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           ),
           bgcolor="#ffffff",
           border_radius=12
       ),
       visible=False
   )

   def get_area_list():
       """地域リストを取得する関数"""
       try:
           #気象庁APIから地域情報を取得
           response = requests.get("https://www.jma.go.jp/bosai/common/const/area.json")
           areas = json.loads(response.text)
           
           #centersの情報を取得
           centers = areas.get("centers", {})
           
           #ドロップダウンの選択肢を設定
           options = []
           for code, info in centers.items():
               name = info.get("name", "")
               if name:
                   options.append(ft.dropdown.Option(key=code, text=name))
           
           area_dropdown.options = options
           page.update()
           
       except Exception as e:
           show_error_dialog(f"エラーが発生しました: {str(e)}")

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
       page.dialog = dlg
       dlg.open = True
       page.update()

   def get_weather(e):
       """天気情報を取得・表示する関数"""
       try:
           selected_code = area_dropdown.value
           if not selected_code:
               return

           #選択された地域のchildren配列から最初の地域コードを取得
           response = requests.get("https://www.jma.go.jp/bosai/common/const/area.json")
           areas = json.loads(response.text)
           centers = areas.get("centers", {})
           selected_center = centers.get(selected_code, {})
           children = selected_center.get("children", [])

           if children:
               #最初の地域コードを使用して天気予報を取得
               weather_code = children[0]
               forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{weather_code}.json"
               forecast_response = requests.get(forecast_url)
               weather_data = json.loads(forecast_response.text)

               if weather_data and len(weather_data) > 0:
                   #天気予報データを解析
                   area_info = weather_data[0]
                   time_series = area_info.get("timeSeries", [])

                   if time_series and len(time_series) > 0:
                       #最初のtimeSeriesから天気情報を取得
                       first_time_series = time_series[0]
                       areas = first_time_series.get("areas", [])

                       if areas and len(areas) > 0:
                           first_area = areas[0]
                           weather = first_area.get("weathers", ["情報なし"])[0]
                           area_name = selected_center.get("name", "不明な地域")

                           #天気情報をカードに表示
                           weather_card.content.content.controls[0].value = f"{area_name}の天気：\n{weather}"
                           weather_card.visible = True
                           page.update()

       except Exception as e:
           show_error_dialog(f"天気情報の取得に失敗しました: {str(e)}")

   #ドロップダウンの変更イベントを設定
   area_dropdown.on_change = get_weather

   #ヘッダー画像の設定
   header_image = ft.Image(
       src="https://www.jma.go.jp/bosai/common/img/logo.svg",
       width=120,
       height=120,
       fit=ft.ImageFit.CONTAIN,
   )

   #画面レイアウトの設定
   page.add(
       ft.Container(
           content=ft.Column(
               controls=[
                   ft.Row(
                       [header_image],
                       alignment=ft.MainAxisAlignment.CENTER
                   ),
                   ft.Text(
                       "気象庁天気予報",
                       size=40,
                       weight=ft.FontWeight.BOLD,
                       color="#1a73e8",
                       text_align=ft.TextAlign.CENTER
                   ),
                   ft.Container(height=20),  #スペース追加
                   ft.Container(
                       content=area_dropdown,
                       alignment=ft.alignment.center
                   ),
                   ft.Container(height=20),  #スペース追加
                   weather_card,
               ],
               horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           ),
           padding=30,
       )
   )

   #初期表示時に地域リストを取得
   get_area_list()

#アプリケーション起動
ft.app(target=main)