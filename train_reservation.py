from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4


@dataclass
class Seat:
    seat_number: str
    class_type: str
    is_booked: bool = False
    passenger_name: Optional[str] = None


@dataclass
class Coach:
    coach_id: str
    class_type: str
    seats: Dict[str, Seat] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.seats:
            for number in range(1, 11):
                seat_number = f"{number:02d}"
                self.seats[seat_number] = Seat(
                    seat_number=seat_number,
                    class_type=self.class_type,
                    is_booked=False,
                    passenger_name=None,
                )


@dataclass
class Train:
    train_id: str
    name: str
    coaches: Dict[str, Coach] = field(default_factory=dict)

    def add_coach(self, coach: Coach) -> None:
        self.coaches[coach.coach_id] = coach

    def get_available_seats(self, class_type: str) -> List[str]:
        available: List[str] = []
        for coach in self.coaches.values():
            if coach.class_type != class_type:
                continue
            for seat in coach.seats.values():
                if not seat.is_booked:
                    available.append(f"{coach.coach_id}-{seat.seat_number}")
        return available


@dataclass
class Booking:
    booking_id: str
    train_id: str
    from_station: str
    to_station: str
    passenger_name: str
    class_type: str
    coach_id: str
    seat_number: str
    booked_at: str


class TrainReservationSystem:
    def __init__(self) -> None:
        self.trains: Dict[str, Train] = {}
        self.bookings: Dict[str, Booking] = {}
        self.lock = Lock()

    def add_train(self, train_id: str, name: str) -> None:
        self.trains[train_id] = Train(train_id=train_id, name=name)

    def add_coach(self, train_id: str, coach_id: str, class_type: str) -> None:
        if train_id not in self.trains:
            raise ValueError(f"Train {train_id} not found")
        coach = Coach(coach_id=coach_id, class_type=class_type)
        self.trains[train_id].add_coach(coach)

    def search_available_seats(self, from_station: str, to_station: str, class_type: str) -> List[dict]:
        del from_station, to_station
        results: List[dict] = []
        for train in self.trains.values():
            available = train.get_available_seats(class_type)
            if available:
                results.append({
                    "train_id": train.train_id,
                    "train_name": train.name,
                    "available_seats": available,
                })
        return results

    def book_ticket(
        self,
        train_id: str,
        from_station: str,
        to_station: str,
        passenger_name: str,
        class_type: str,
    ) -> Booking:
        with self.lock:
            train = self.trains.get(train_id)
            if train is None:
                raise ValueError(f"Train {train_id} not found")

            selected_coach: Optional[Coach] = None
            selected_seat: Optional[Seat] = None

            for coach in train.coaches.values():
                if coach.class_type != class_type:
                    continue
                for seat in coach.seats.values():
                    if not seat.is_booked:
                        selected_coach = coach
                        selected_seat = seat
                        break
                if selected_coach is not None and selected_seat is not None:
                    break

            if selected_coach is None or selected_seat is None:
                raise ValueError(f"No available seat found for class {class_type}")

            booking_id = str(uuid4())[:8]
            booking = Booking(
                booking_id=booking_id,
                train_id=train_id,
                from_station=from_station,
                to_station=to_station,
                passenger_name=passenger_name,
                class_type=class_type,
                coach_id=selected_coach.coach_id,
                seat_number=selected_seat.seat_number,
                booked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            selected_seat.is_booked = True
            selected_seat.passenger_name = passenger_name
            self.bookings[booking_id] = booking
            return booking

    def cancel_booking(self, booking_id: str) -> bool:
        with self.lock:
            booking = self.bookings.get(booking_id)
            if booking is None:
                raise ValueError(f"Booking {booking_id} not found")

            train = self.trains.get(booking.train_id)
            if train is None:
                raise ValueError(f"Train {booking.train_id} not found")

            for coach in train.coaches.values():
                if coach.coach_id != booking.coach_id:
                    continue
                seat = coach.seats.get(booking.seat_number)
                if seat:
                    seat.is_booked = False
                    seat.passenger_name = None
                    break

            del self.bookings[booking_id]
            return True

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self.bookings.get(booking_id)


def demo() -> None:
    system = TrainReservationSystem()
    system.add_train("101", "Express 101")
    system.add_coach("101", "A1", "Sleeper")
    system.add_coach("101", "A2", "Sleeper")
    system.add_coach("101", "B1", "AC")

    print("Train 101: Express 101")
    print("Available Sleeper seats for Delhi -> Mumbai:")
    print(system.search_available_seats("Delhi", "Mumbai", "Sleeper"))

    booking = system.book_ticket(
        train_id="101",
        from_station="Delhi",
        to_station="Mumbai",
        passenger_name="Alice",
        class_type="Sleeper",
    )
    print("Booking created:")
    print(booking)

    print("Available Sleeper seats after booking:")
    print(system.search_available_seats("Delhi", "Mumbai", "Sleeper"))

    print("Cancel booking:")
    print(system.cancel_booking(booking.booking_id))
    print(system.search_available_seats("Delhi", "Mumbai", "Sleeper"))


if __name__ == "__main__":
    demo()

