import sys
import calendar
from datetime import datetime, date, time
import os
import winreg
import traceback
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtWidgets import (
    QApplication, QDialog, QGridLayout, 
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    QCheckBox, QSlider, QFormLayout, QSystemTrayIcon, QMenu, QAction, QStyle, QMessageBox
)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(300, 260)
        self.parent_widget = parent
        self.setStyleSheet("QDialog { background-color: #2b3035; color: #ffffff; border-radius: 10px; } QLabel { color: #ffffff; font-size: 13px; } QCheckBox { color: #ffffff; spacing: 8px; } QPushButton { background-color: #34495e; color: #ffffff; border-radius: 6px; padding: 6px 14px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); } QPushButton:hover { background-color: #2980b9; }")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.ontop_chk = QCheckBox("窗口总在最前端")
        self.ontop_chk.setChecked(True)
        self.ontop_chk.stateChanged.connect(self.toggle_ontop)
        form_layout.addRow(self.ontop_chk)

        self.hide_chk = QCheckBox("关闭时隐藏到托盘")
        self.hide_chk.setChecked(True)
        self.hide_chk.stateChanged.connect(self.toggle_hide)
        form_layout.addRow(self.hide_chk)

        self.autostart_chk = QCheckBox("开机自动启动")
        self.autostart_chk.setChecked(self.check_autostart_status())
        self.autostart_chk.stateChanged.connect(self.toggle_autostart)
        form_layout.addRow(self.autostart_chk)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(245)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        form_layout.addRow("背景透明度:", self.opacity_slider)

        layout.addLayout(form_layout)
        close_btn = QPushButton("确定")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def toggle_ontop(self, state):
        if self.parent_widget:
            flags = self.parent_widget.windowFlags()
            if state == Qt.Checked:
                self.parent_widget.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            else:
                self.parent_widget.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.parent_widget.show()

    def toggle_hide(self, state):
        if self.parent_widget:
            self.parent_widget.close_to_tray = (state == Qt.Checked)

    def check_autostart_status(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MarketClockWidget"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_autostart(self, state):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MarketClockWidget"
        script_path = os.path.abspath(sys.argv[0])
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        cmd = f'"{python_exe}" "{script_path}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if state == Qt.Checked:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except WindowsError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print("设置开机自启失败:", e)

    def change_opacity(self, value):
        if self.parent_widget:
            style = "QWidget { background-color: rgba(43, 48, 53, " + str(value) + "); border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); }"
            self.parent_widget.card.setStyleSheet(style)


class CalendarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("A股/港股动态休市日历（点击日期查看原因）")
        self.setFixedSize(460, 580)
        
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month

        self.setStyleSheet("QDialog { background-color: #2b3035; color: #ffffff; border-radius: 12px; } QLabel { color: #ffffff; font-size: 13px; } QPushButton { background-color: #34495e; color: #ffffff; border-radius: 6px; padding: 6px 14px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); } QPushButton:hover { background-color: #2980b9; }")

        layout = QVBoxLayout(self)
        top_bar = QWidget()
        top_bar.setStyleSheet("QWidget { background-color: #1f3a60; border-radius: 8px; padding: 4px; }")
        top_layout = QHBoxLayout(top_bar)
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(36, 30)
        self.prev_btn.clicked.connect(self.prev_month)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(36, 30)
        self.next_btn.clicked.connect(self.next_month)
        
        self.month_title = QLabel()
        self.month_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.month_title.setAlignment(Qt.AlignCenter)
        
        top_layout.addWidget(self.prev_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.month_title)
        top_layout.addStretch()
        top_layout.addWidget(self.next_btn)
        layout.addWidget(top_bar)

        week_widget = QWidget()
        week_layout = QGridLayout(week_widget)
        week_layout.setContentsMargins(0, 5, 0, 5)
        weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        for i, w in enumerate(weekdays):
            lbl = QLabel(w)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;" if i in [0, 6] else "color: #d0d0d0; font-size: 14px; font-weight: bold;")
            week_layout.addWidget(lbl, 0, i)
        layout.addWidget(week_widget)

        self.days_widget = QWidget()
        self.days_layout = QGridLayout(self.days_widget)
        self.days_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.days_widget)

        legend_widget = QWidget()
        legend_layout = QHBoxLayout(legend_widget)
        legend_layout.setContentsMargins(5, 0, 5, 0)
        legend_layout.addStretch()
        legend_layout.addWidget(QLabel("🟢 周末固定休市"))
        legend_layout.addStretch()
        legend_layout.addWidget(QLabel("🔴 A股休市"))
        legend_layout.addStretch()
        legend_layout.addWidget(QLabel("🟣 港股休市"))
        legend_layout.addStretch()
        layout.addWidget(legend_widget)

        close_btn = QPushButton("关闭面板")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.update_calendar_grid()

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar_grid()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar_grid()

    @staticmethod
    def get_holiday_info(year, month, day):
        current_date = date(year, month, day)
        weekday = current_date.weekday()
        is_weekend = (weekday >= 5)
        
        markers = []
        tips = []
        
        if is_weekend:
            tips.append("周末固定休市")
            
        if year == 2026:
            if month == 1:
                if day in [1, 2] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("元旦休市 (A股/港股)")
            elif month == 2:
                if 16 <= day <= 20 and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("春节休市 (A股/港股)")
            elif month == 4:
                if day in [3, 6] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("清明节休市 (A股/港股)")
            elif month == 5:
                if day in [1, 4, 5] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("劳动节休市 (A股/港股)")
            elif month == 6:
                if day in [19, 22] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("端午节休市 (A股/港股)")
            elif month == 9:
                if day in [25, 28] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("中秋节休市 (A股/港股)")
            elif month == 10:
                if 1 <= day <= 7 and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("国庆节休市 (A股/港股)")
            elif month == 12:
                if day in [24, 25, 31] and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市 (圣诞节/新年前夕)")

        elif year == 2027:
            if month == 1:
                if day in [1, 2] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("元旦休市 (A股/港股)")
            elif month == 2:
                if (day == 5 or 8 <= day <= 12) and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("春节休市 (A股/港股)")
            elif month == 3:
                if day in [26, 29] and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市 (耶稣受难节/复活节)")
            elif month == 4:
                if day == 5 and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("清明节休市 (A股/港股)")
                elif day == 29 and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市")
            elif month == 5:
                if day in [3, 4, 5] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("劳动节休市 (A股/港股)")
                elif day == 13 and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市")
            elif month == 6:
                if day == 9 and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("端午节休市 (A股/港股)")
                elif day == 30 and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市")
            elif month == 7:
                if day == 1 and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市")
            elif month == 9:
                if day in [15, 16, 30] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("中秋节休市 (A股/港股)")
            elif month == 10:
                if 1 <= day <= 7 and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("国庆节休市 (A股/港股)")
                elif day == 8 and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市 (重阳节)")
            elif month == 12:
                if day in [24, 27, 31] and not is_weekend:
                    markers.append("🟣")
                    tips.append("港股休市 (圣诞节)")

        elif year == 2028:
            if month == 1:
                if day in [1, 2, 3] and not is_weekend:
                    markers.extend(["🔴", "🟣"])
                    tips.append("元旦休市 (A股/港股)")

        marker_str = f"{day}\n" + "".join(markers) if markers else str(day)
        tip_str = f"{year}年{month}月{day}日休市原因：\n" + "\n".join(tips) if tips else f"{year}年{month}月{day}日：正常交易日"
        return marker_str, tip_str, is_weekend, len(markers) > 0

    def update_calendar_grid(self):
        self.month_title.setText(f"{self.current_year}年 {self.current_month}月")
        for i in reversed(range(self.days_layout.count())):
            w = self.days_layout.itemAt(i).widget()
            if w: w.setParent(None)

        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)
        
        for r_idx, week in enumerate(month_days):
            for c_idx, day in enumerate(week):
                if day == 0:
                    btn = QPushButton("")
                    btn.setEnabled(False)
                else:
                    marker, tip, is_weekend, is_holiday = CalendarDialog.get_holiday_info(self.current_year, self.current_month, day)
                    btn = QPushButton(marker)
                    btn.clicked.connect(lambda checked, t=tip: QMessageBox.information(self, "日期休市详情", t))
                    
                    if is_weekend:
                        btn.setStyleSheet("background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border-radius: 6px; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.3);")
                    elif is_holiday:
                        btn.setStyleSheet("background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border-radius: 6px; font-weight: bold; border: 1px solid rgba(231, 76, 60, 0.3);")
                    else:
                        btn.setStyleSheet("background-color: #34495e; color: #ffffff; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);")

                btn.setFixedHeight(50)
                self.days_layout.addWidget(btn, r_idx, c_idx)


class MarketClockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.is_locked = False
        self.close_to_tray = True
        self.init_ui()
        self.init_tray()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.card = QWidget()
        self.card.setStyleSheet("QWidget { background-color: rgba(43, 48, 53, 245); border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); }")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        self.lock_btn = QPushButton("🔓")
        self.lock_btn.setFixedSize(26, 26)
        self.lock_btn.setToolTip("锁定窗口位置")
        self.lock_btn.setStyleSheet("QPushButton { background: transparent; color: #ffffff; border: none; font-size: 14px; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }")
        self.lock_btn.clicked.connect(self.toggle_lock)
        
        self.setting_btn = QPushButton("⚙")
        self.setting_btn.setFixedSize(26, 26)
        self.setting_btn.setToolTip("设置")
        self.setting_btn.setStyleSheet("QPushButton { background: transparent; color: #ffffff; border: none; font-size: 14px; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }")
        self.setting_btn.clicked.connect(self.open_settings)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("关闭")
        close_btn.setStyleSheet("QPushButton { background: transparent; color: #ffffff; border: none; font-size: 14px; } QPushButton:hover { background: rgba(231,76,60,0.8); border-radius: 4px; }")
        close_btn.clicked.connect(self.close)
        
        top_bar.addWidget(self.lock_btn)
        top_bar.addWidget(self.setting_btn)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        card_layout.addLayout(top_bar)

        self.weekday_label = QLabel("星期一")
        self.weekday_label.setAlignment(Qt.AlignCenter)
        self.weekday_label.setStyleSheet("color: #ffffff; font-size: 32px; font-weight: bold;")
        card_layout.addWidget(self.weekday_label)

        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #ffffff; font-size: 44px; font-weight: 300;")
        card_layout.addWidget(self.time_label)

        self.date_label = QLabel("2026年11月03日")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("color: #d0d0d0; font-size: 16px;")
        card_layout.addWidget(self.date_label)

        footer_layout = QHBoxLayout()
        self.market_status_label = QLabel("📈 股市: 检查中...")
        self.market_status_label.setStyleSheet("color: #2ecc71; font-size: 12px; font-weight: bold;")
        
        self.holiday_btn = QPushButton("📅 查看休市日历")
        self.holiday_btn.setMinimumWidth(210)
        self.holiday_btn.setStyleSheet("QPushButton { background-color: rgba(255, 255, 255, 0.08); color: #e74c3c; font-size: 12px; font-weight: bold; border: 1px solid rgba(231, 76, 60, 0.3); border-radius: 6px; padding: 4px 8px; text-align: center; } QPushButton:hover { background-color: rgba(231, 76, 60, 0.2); color: #ffffff; }")
        self.holiday_btn.clicked.connect(lambda: CalendarDialog(self).exec_())
        
        footer_layout.addWidget(self.market_status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.holiday_btn)
        card_layout.addLayout(footer_layout)

        self.countdown_label = QLabel("未开盘")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold; margin-top: 4px;")
        card_layout.addWidget(self.countdown_label)
        
        main_layout.addWidget(self.card)
        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()
        self.resize(360, 310)

    def init_tray(self):
        try:
            icon = self.style().standardIcon(QStyle.SP_FileDialogInfoView)
            self.tray_icon = QSystemTrayIcon(icon, self)
            self.tray_icon.setToolTip("A股市场监控时钟")

            tray_menu = QMenu()
            show_action = QAction("显示主界面", self)
            show_action.triggered.connect(self.showNormal)
            quit_action = QAction("完全退出", self)
            quit_action.triggered.connect(QApplication.quit)

            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            print("托盘初始化提示:", e)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.raise_()

    def closeEvent(self, event):
        if self.close_to_tray:
            event.ignore()
            self.hide()
        else:
            event.accept()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.setText("🔒")
            self.lock_btn.setToolTip("已锁定窗口位置（点击解锁）")
        else:
            self.lock_btn.setText("🔓")
            self.lock_btn.setToolTip("锁定窗口位置")

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

    def is_a_share_closed_today(self, now):
        if now.weekday() >= 5:
            return True
        marker, _, _, is_holiday = CalendarDialog.get_holiday_info(now.year, now.month, now.day)
        if is_holiday or "🔴" in marker:
            return True
        return False

    def update_clock(self):
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.weekday_label.setText(weekdays[now.weekday()])
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y年%m月%d日"))
        
        t_str = now.strftime("%H:%M")
        is_closed = self.is_a_share_closed_today(now)

        if is_closed:
            if now.weekday() >= 5:
                self.market_status_label.setText("🔴 股市: 周末休市")
            else:
                self.market_status_label.setText("🔴 股市: 节假日休市")
            self.market_status_label.setStyleSheet("color: #e74c3c;")
            self.countdown_label.setText("今日休市")
        else:
            if "09:15" <= t_str <= "11:30":
                self.market_status_label.setText("🟢 股市: 交易中")
                self.market_status_label.setStyleSheet("color: #2ecc71;")
                target_time = datetime.combine(now.date(), time(11, 30, 0))
                diff = target_time - now
                secs = int(diff.total_seconds())
                if secs > 0:
                    h, rem = divmod(secs, 3600)
                    m, s = divmod(rem, 60)
                    self.countdown_label.setText(f"距上午收盘 {h:02d}:{m:02d}:{s:02d}")
                else:
                    self.countdown_label.setText("上午已收盘")
            elif "13:00" <= t_str <= "15:00":
                self.market_status_label.setText("🟢 股市: 交易中")
                self.market_status_label.setStyleSheet("color: #2ecc71;")
                target_time = datetime.combine(now.date(), time(15, 0, 0))
                diff = target_time - now
                secs = int(diff.total_seconds())
                if secs > 0:
                    h, rem = divmod(secs, 3600)
                    m, s = divmod(rem, 60)
                    self.countdown_label.setText(f"距下午收盘 {h:02d}:{m:02d}:{s:02d}")
                else:
                    self.countdown_label.setText("今日已收盘")
            else:
                self.market_status_label.setText("🟡 股市: 非交易时段")
                self.market_status_label.setStyleSheet("color: #f1c40f;")
                if t_str < "09:15":
                    self.countdown_label.setText("未开盘")
                elif "11:30" < t_str < "13:00":
                    self.countdown_label.setText("午间休市中")
                else:
                    self.countdown_label.setText("今日已收盘")

    def mousePressEvent(self, event):
        if not self.is_locked and event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.is_locked and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        app.setQuitOnLastWindowClosed(False)
        clock = MarketClockWidget()
        clock.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = traceback.format_exc()
        print(error_msg)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("程序运行出错")
        msg.setText("程序发生异常崩溃：")
        msg.setDetailedText(error_msg)
        msg.exec_()