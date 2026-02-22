from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker
from datetime import date, timedelta

KV = '''
ScreenManager:
    CalendarScreen:
    TasksScreen:
    AnalyticsScreen:
    MoneyScreen:

<CalendarScreen>:
    name: "calendar"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Календарь и ежедневник"
            right_action_items: [["calendar", root.open_calendar]]

        MDLabel:
            id: selected_date
            text: "Выбери дату"
            halign: "center"
            font_style: "H5"
            size_hint_y: None
            height: dp(50)

        MDRaisedButton:
            text: "Перейти к задачам"
            pos_hint: {"center_x": 0.5}
            on_release: root.go_to_tasks()

        MDRaisedButton:
            text: "Аналитика"
            pos_hint: {"center_x": 0.5}
            on_release: root.go_to_analytics()

        MDRaisedButton:
            text: "Учёт денег"
            pos_hint: {"center_x": 0.5}
            on_release: root.go_to_money()


<TasksScreen>:
    name: "tasks"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Задачи на день"
            left_action_items: [["arrow-left", root.back_to_calendar]]

        ScrollView:
            MDList:
                id: tasks_list

        MDRaisedButton:
            text: "Добавить задачу"
            size_hint_y: None
            height: dp(50)
            on_release: root.add_task()


<AnalyticsScreen>:
    name: "analytics"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Аналитика"
            left_action_items: [["arrow-left", root.back_to_calendar]]

        MDLabel:
            id: analytics_label
            halign: "center"
            text: "Здесь будет аналитика"


<MoneyScreen>:
    name: "money"

    MDBoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        MDTopAppBar:
            title: "Учёт денег"
            left_action_items: [["arrow-left", root.back_to_calendar]]

        MDTextField:
            id: money_amount
            hint_text: "Сумма"

        MDTextField:
            id: money_comment
            hint_text: "Комментарий"

        MDRaisedButton:
            text: "Добавить расход"
            on_release: root.add_money()

        MDLabel:
            id: money_total
            halign: "center"
            text: "Всего потрачено: 0"
'''

# ---------------------- Python код ----------------------

class CalendarScreen(Screen):
    selected_date = None

    def open_calendar(self, *args):
        picker = MDDatePicker()
        picker.bind(on_save=self.on_save)
        picker.open()

    def on_save(self, instance, value, date_range):
        self.selected_date = value
        self.ids.selected_date.text = value.strftime("%A, %d %B %Y")
        MDApp.get_running_app().current_date = value

    def go_to_tasks(self, *args):
        if self.selected_date:
            MDApp.get_running_app().root.current = "tasks"

    def go_to_analytics(self, *args):
        MDApp.get_running_app().root.current = "analytics"

    def go_to_money(self, *args):
        MDApp.get_running_app().root.current = "money"


class TasksScreen(Screen):
    def on_enter(self):
        self.load_tasks()

    def load_tasks(self):
        self.ids.tasks_list.clear_widgets()
        app = MDApp.get_running_app()
        tasks = app.data.get(app.current_date, [])
        for t in tasks:
            box = MDBoxLayout(orientation="horizontal", adaptive_height=True)
            checkbox = MDCheckbox(active=t.get("done", False))
            checkbox.bind(active=lambda cb, value, task=t: self.toggle_task(task, value))
            item = OneLineListItem(text=t["title"])
            item.bind(on_release=lambda x, task=t: self.edit_algorithm(task))
            box.add_widget(checkbox)
            box.add_widget(item)
            self.ids.tasks_list.add_widget(box)

    def toggle_task(self, task, value):
        task["done"] = value
        self.load_tasks()

    def add_task(self):
        self.task_field = MDTextField(hint_text="Название задачи", multiline=False)
        self.dialog = MDDialog(
            title="Новая задача",
            type="custom",
            content_cls=self.task_field,
            buttons=[
                MDRaisedButton(text="Отмена", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="Далее", on_release=self.save_task)
            ]
        )
        self.dialog.open()

    def save_task(self, *args):
        title = self.task_field.text.strip()
        if not title:
            return
        app = MDApp.get_running_app()
        task = {"title": title, "algorithm": [], "done": False}
        app.data.setdefault(app.current_date, []).append(task)
        self.dialog.dismiss()
        self.load_tasks()

    def edit_algorithm(self, task):
        alg_text = "\n".join(task.get("algorithm", []))
        self.alg_field = MDTextField(
            text=alg_text,
            hint_text="Алгоритм выполнения (до 50 строк)",
            multiline=True
        )
        self.alg_dialog = MDDialog(
            title="Алгоритм выполнения",
            type="custom",
            content_cls=self.alg_field,
            buttons=[
                MDRaisedButton(text="Сохранить", on_release=lambda x: self.save_algorithm(task))
            ]
        )
        self.alg_dialog.open()

    def save_algorithm(self, task):
        lines = self.alg_field.text.split("\n")[:50]
        task["algorithm"] = lines
        self.alg_dialog.dismiss()

    def back_to_calendar(self, *args):
        self.manager.current = "calendar"


class AnalyticsScreen(Screen):
    def on_enter(self):
        self.update_analytics()

    def update_analytics(self):
        app = MDApp.get_running_app()
        completed = 0
        pending = 0
        weekly_pending = 0
        today = date.today()
        week_ago = today - timedelta(days=7)
        for day, tasks in app.data.items():
            for t in tasks:
                if t.get("done"):
                    completed += 1
                else:
                    pending += 1
                if day >= week_ago and not t.get("done"):
                    weekly_pending += 1
        self.ids.analytics_label.text = (
            f"Выполнено задач: {completed}\n"
            f"Невыполнено задач: {pending}\n"
            f"Невыполнено за последнюю неделю: {weekly_pending}"
        )

    def back_to_calendar(self, *args):
        self.manager.current = "calendar"


class MoneyScreen(Screen):
    def add_money(self):
        try:
            amount = float(self.ids.money_amount.text)
        except:
            return
        comment = self.ids.money_comment.text
        app = MDApp.get_running_app()
        app.money.append({"amount": amount, "comment": comment})
        total = sum(m["amount"] for m in app.money)
        self.ids.money_total.text = f"Всего потрачено: {total}"

    def back_to_calendar(self, *args):
        self.manager.current = "calendar"


class PlannerApp(MDApp):
    data = {}  # {дата: [список задач]}
    current_date = None
    money = []

    def build(self):
        return Builder.load_string(KV)


PlannerApp().run()