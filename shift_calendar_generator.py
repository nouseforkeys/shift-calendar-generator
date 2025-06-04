"""
creates calendar events for shift work
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import (QApplication, QCalendarWidget, QFileDialog,
                             QGridLayout, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QStyle, QTimeEdit, QVBoxLayout,
                             QWidget)

log = logging.getLogger(Path(__file__).name)
logging.basicConfig(level=logging.INFO)


@dataclass
class Event:
    """container for an event"""
    organiser: str
    dtstart: datetime
    dtend: datetime
    summary: str
    dtstamp: datetime = None
    uid: UUID = None

    DT_FORMAT = '%Y%m%dT%H%M%S'

    def __post_init__(self):
        if self.uid is None:
            self.uid = uuid4()
        if self.dtstamp is None:
            self.dtstamp = datetime.now()

    def to_str(self) -> str:
        """
        converts this object to the event portion of an iCalendar file string
        """
        content = ['BEGIN:VEVENT']
        content.append(f'UID:{self.uid}')
        content.append(f'ORGANIZER:{self.organiser}')
        content.append(f'DTSTAMP:{self.dtstamp.strftime(self.DT_FORMAT)}')
        content.append(f'DTSTART:{self.dtstart.strftime(self.DT_FORMAT)}')
        content.append(f'DTEND:{self.dtend.strftime(self.DT_FORMAT)}')
        content.append(f'SUMMARY:{self.summary}')
        content.append('END:VEVENT')

        return '\n'.join(content)

    def gui_str(self) -> str:
        """formats the start date as a nice str for the gui"""
        return (
            f'{self.dtstart.strftime('%d %b %Y')} '
            f'{self.dtstart.strftime('%I:%M %p')} - '
            f'{self.dtend.strftime('%I:%M %p')}'
        )

    def __lt__(self, other: 'Event') -> bool:
        return self.dtstart < other.dtstart

    def __eq__(self, other: 'Event') -> bool:
        return self.dtstart == other.dtstart


@dataclass
class Calendar:
    """basis for creating an iCalendar event file"""
    prodid: str
    version: str = '2.0'
    events: list[Event] = None

    def __post_init__(self):
        if self.events is None:
            self.events = list()

    def to_str(self) -> str:
        """converts this object to an iCalendar file string"""
        content = ['BEGIN:VCALENDAR']
        content.append(f'VERSION:{self.version}')
        content.append(f'PRODID:{self.prodid}')
        for event in sorted(self.events):
            content.append(event.to_str())
        content.append('END:VCALENDAR')

        return '\n'.join(content)

    def to_file(self, filename: Path) -> None:
        """saves this object to an iCalendar file"""
        save_to = filename.with_suffix('.ics')
        with open(save_to, 'w') as file:
            file.write(self.to_str())
        log.info(f'saved to "{save_to}"')


class EventLayout(QHBoxLayout):
    """stores a label for showing the event time and a delete button"""
    def __init__(self, event: Event, delete_func: callable):
        super().__init__()
        self.event = event
        self.delete_func = delete_func

        label = QLabel()
        label.setText(event.gui_str())
        delete_button = QPushButton()
        bin_pxmap = QStyle.StandardPixmap.SP_DialogCancelButton
        bin_icon = delete_button.style().standardIcon(bin_pxmap)
        delete_button.setIcon(bin_icon)
        delete_button.setFixedWidth(50)
        delete_button.clicked.connect(self.delete_this_event)

        self.widgets = [label, delete_button]
        for widget in self.widgets:
            self.addWidget(widget)

    def remove(self) -> None:
        """deletes the label and button widgets for removal"""
        for widget in self.widgets:
            self.removeWidget(widget)

    def delete_this_event(self) -> None:
        """deletes this event from the list of shifts"""
        self.remove()
        self.delete_func()
        log.info(f'deleted event: {self.event.gui_str()}')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Path(__file__).name)

        layout = QHBoxLayout()
        controls = QVBoxLayout()
        self.shifts = QVBoxLayout()
        self.shift_events = []

        add_button = QPushButton('Add event')
        add_button.clicked.connect(self.add_event)
        add_button.setFixedHeight(100)

        del_button = QPushButton('Delete last event')
        del_button.clicked.connect(self.delete_last_event)

        self.save_dialog = QFileDialog()
        self.save_dialog.setDefaultSuffix('.ics')

        save_button = QPushButton('Save to file...')
        save_button.clicked.connect(self.save_to_file)

        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(7, 0))

        self.end_time_input = QTimeEdit()
        self.end_time_input.setTime(QTime(20, 0))

        time_grid = QGridLayout()
        start_label = QLabel()
        start_label.setText('Start time:')
        end_label = QLabel()
        end_label.setText('End time:')
        time_grid.addWidget(start_label, 0, 0)
        time_grid.addWidget(self.start_time_input, 0, 1)
        time_grid.addWidget(end_label, 1, 0)
        time_grid.addWidget(self.end_time_input, 1, 1)

        self.date_input = QCalendarWidget()

        controls.addLayout(time_grid)
        controls.addWidget(self.date_input)
        controls.addWidget(save_button)
        controls.addWidget(del_button)
        controls.addWidget(add_button)

        shifts_title = QLabel()
        shifts_title.setFixedWidth(300)
        shifts_title.setText('Shifts:')
        self.shifts.addWidget(shifts_title)
        # add a streched empty widget for padding
        self.shifts.addWidget(QWidget(), 1)

        layout.addLayout(controls)
        layout.addLayout(self.shifts)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.calendar = Calendar(Path(__file__).name)

    def add_event(self) -> None:
        """adds an event with the current time settings"""
        start_time = self.start_time_input.time()
        end_time = self.end_time_input.time()
        date = self.date_input.selectedDate()

        start_datetime = datetime(
            year=date.year(), month=date.month(), day=date.day(),
            hour=start_time.hour(), minute=start_time.minute(),
        )
        end_datetime = datetime(
            year=date.year(), month=date.month(), day=date.day(),
            hour=end_time.hour(), minute=end_time.minute(),
        )

        event = Event(
            organiser=Path(__file__).name,
            dtstart=start_datetime,
            dtend=end_datetime,
            summary='long day'
        )
        self.calendar.events.append(event)
        self.shift_events.append(
            EventLayout(event, self.get_delete_func(event)))
        self.update_shifts()
        log.info(f'added event: {event.gui_str()}')

    def delete_last_event(self) -> None:
        """deletes the most recently added event from the calendar"""
        if len(self.calendar.events) > 0:
            event = self.calendar.events.pop()
            for event_layout in self.shift_events:
                if event_layout.event == event:
                    break
            self.update_shifts()
            log.info(f'deleted last event: {event.gui_str()}')

    def get_delete_func(self, event: Event) -> callable:
        """returns a func that an EventLayout can use to delete itself"""
        def delete_func() -> None:
            self.calendar.events.remove(event)
            self.update_shifts()
        return delete_func

    def save_to_file(self) -> None:
        """opens a file dialog and saves the file to the specified filename"""
        from_dialog = self.save_dialog.getSaveFileName()[0]
        if from_dialog != '':
            self.calendar.to_file(Path(from_dialog))
        else:
            log.warning('Save dialog closed. File not saved!')

    def update_shifts(self) -> None:
        """removes and re-adds the shift events"""
        for event_layout in self.shift_events:
            event_layout.remove()
            self.shifts.removeItem(event_layout)
        self.shift_events = []
        for event in sorted(self.calendar.events):
            event_layout = EventLayout(event, self.get_delete_func(event))
            # insert widgets 1 before last as it is a padding widget
            self.shifts.insertLayout(self.shifts.count() - 1, event_layout)
            self.shift_events.append(event_layout)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
