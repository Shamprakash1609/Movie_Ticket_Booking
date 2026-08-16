import os
from Modules.Notifications.ObserverInterface import Subject, Observer
from Modules.Auth.UserDAO import UserDAO
from Modules.Common.Enums import UserRole


class NotificationService(Subject):
    def __init__(self):
        self._observers = []
        self._message = ""
        # Currently treating the console logging as our "CustomerObserver"
        # since it's a CLI app without actual push notifications.
        # But we maintain the structure.

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        # Mirrors attach()'s guard; list.remove raises ValueError on an unknown observer.
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self._message)

    def notify_customers_of_new_movie(self, movie_title):
        self._message = f"[NOTIFICATION] A new movie '{movie_title}' has been added!"
        self.notify()


class ConsoleCustomerObserver(Observer):
    """A concrete observer that logs to the console."""

    def update(self, message):
        try:
            # Save log relative to the app directory instead of CWD (e.g. C:\Users)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_file = os.path.join(base_dir, "notifications.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception:
            # Fallback to standard console print if file write fails
            print(f"\n{message}")
