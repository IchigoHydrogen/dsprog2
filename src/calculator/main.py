import flet as ft
import math

#基本的な計算ボタンの定義
class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text

#数字ボタンのスタイル定義
class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.colors.WHITE24
        self.color = ft.colors.WHITE

#演算ボタンのスタイル定義
class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.ORANGE
        self.color = ft.colors.WHITE

#その他機能ボタンのスタイル定義
class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.BLUE_GREY_100
        self.color = ft.colors.BLACK

#科学計算ボタンのスタイル定義
class ScienceButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.DEEP_PURPLE_100
        self.color = ft.colors.BLACK

class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        #結果表示部分の設定
        self.result = ft.Text(value="0", color=ft.colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        
        #電卓のレイアウト設定
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                #科学計算ボタン行の追加
                ft.Row(
                    controls=[
                        ScienceButton(text="√", button_clicked=self.button_clicked),
                        ScienceButton(text="x²", button_clicked=self.button_clicked),
                        ScienceButton(text="ln", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScienceButton(text="sin", button_clicked=self.button_clicked),
                        ScienceButton(text="cos", button_clicked=self.button_clicked),
                        ScienceButton(text="tan", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    def button_clicked(self, e):
        data = e.control.data
        
        #エラー時やACボタン押下時のリセット処理
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        #数字や小数点の入力処理
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = self.result.value + data

        #基本的な四則演算の処理
        elif data in ("+", "-", "*", "/"):
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        #科学計算機能の処理
        elif data in ("√", "x²", "ln", "sin", "cos", "tan"):
            try:
                value = float(self.result.value)
                if data == "√":
                    if value < 0:
                        self.result.value = "Error"
                    else:
                        self.result.value = self.format_number(math.sqrt(value))
                elif data == "x²":
                    self.result.value = self.format_number(value ** 2)
                elif data == "ln":
                    if value <= 0:
                        self.result.value = "Error"
                    else:
                        self.result.value = self.format_number(math.log(value))
                elif data == "sin":
                    self.result.value = self.format_number(math.sin(math.radians(value)))
                elif data == "cos":
                    self.result.value = self.format_number(math.cos(math.radians(value)))
                elif data == "tan":
                    self.result.value = self.format_number(math.tan(math.radians(value)))
            except:
                self.result.value = "Error"
            self.reset()

        #イコールボタンの処理
        elif data == "=":
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.reset()

        #パーセント計算の処理
        elif data == "%":
            self.result.value = float(self.result.value) / 100
            self.reset()

        #符号反転の処理
        elif data == "+/-":
            if float(self.result.value) > 0:
                self.result.value = "-" + str(self.result.value)
            elif float(self.result.value) < 0:
                self.result.value = str(self.format_number(abs(float(self.result.value))))

        self.update()

    #数値フォーマットの処理
    def format_number(self, num):
        if num % 1 == 0:
            return int(num)
        else:
            return round(num, 8)  #小数点以下8桁までに制限

    #基本計算処理
    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return self.format_number(operand1 + operand2)
        elif operator == "-":
            return self.format_number(operand1 - operand2)
        elif operator == "*":
            return self.format_number(operand1 * operand2)
        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)

    #状態のリセット
    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True

def main(page: ft.Page):
    page.title = "Scientific Calculator"
    calc = CalculatorApp()
    page.add(calc)

ft.app(target=main)