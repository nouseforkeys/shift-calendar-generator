"""
creates calendar events for shift work
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDateEdit, QTimeEdit, QPushButton, QHBoxLayout,
    QWidget
)

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
        for event in self.events:
            content.append(event.to_str())
        content.append('END:VCALENDAR')

        return '\n'.join(content)

    def to_file(self, filename: Path) -> None:
        """saves this object to an iCalendar file"""
        save_to = filename.with_suffix('.ics')
        with open(save_to, 'w') as file:
            file.write(self.to_str())
        log.info(f'saved to "{save_to}"')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Path(__file__).name)

        layout = QHBoxLayout()
        add_button = QPushButton('Add event')
        del_button = QPushButton('Delete last event')
        start_time = QTimeEdit()
        end_time = QTimeEdit()
        date_edit = QDateEdit()
        layout.addWidget(add_button)
        layout.addWidget(del_button)
        layout.addWidget(start_time)
        layout.addWidget(end_time)
        layout.addWidget(date_edit)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
