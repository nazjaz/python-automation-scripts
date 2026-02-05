"""Itinerary document generation service."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from src.database import DatabaseManager, Itinerary

logger = logging.getLogger(__name__)


class ItineraryGenerator:
    """Service for generating itinerary documents."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        output_directory: str = "itineraries",
        template_path: Optional[str] = None,
    ):
        """Initialize itinerary generator.

        Args:
            db_manager: Database manager instance.
            output_directory: Directory for output files.
            template_path: Path to HTML template directory.
        """
        self.db_manager = db_manager
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        if template_path:
            self.template_env = Environment(
                loader=FileSystemLoader(Path(template_path).parent)
            )
        else:
            template_dir = Path(__file__).parent.parent / "templates"
            self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def generate_html(self, itinerary_id: int, filename: Optional[str] = None) -> Path:
        """Generate HTML itinerary.

        Args:
            itinerary_id: Itinerary ID.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated HTML file.
        """
        itinerary = self.db_manager.get_itinerary(itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {itinerary_id} not found")

        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"itinerary_{itinerary_id}_{timestamp}.html"

        output_path = self.output_directory / filename

        with self.db_manager.get_session() as session:
            from src.database import FlightBooking, HotelBooking, ActivityBooking

            flights = (
                session.query(FlightBooking)
                .filter(FlightBooking.itinerary_id == itinerary_id)
                .all()
            )
            hotels = (
                session.query(HotelBooking)
                .filter(HotelBooking.itinerary_id == itinerary_id)
                .all()
            )
            activities = (
                session.query(ActivityBooking)
                .filter(ActivityBooking.itinerary_id == itinerary_id)
                .all()
            )

        try:
            template = self.template_env.get_template("itinerary.html")
        except TemplateNotFound:
            html_content = self._generate_default_html(
                itinerary, flights, hotels, activities
            )
        else:
            html_content = template.render(
                itinerary=itinerary,
                flights=flights,
                hotels=hotels,
                activities=activities,
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Generated HTML itinerary: {output_path}")
        return output_path

    def generate_pdf(self, itinerary_id: int, filename: Optional[str] = None) -> Path:
        """Generate PDF itinerary.

        Args:
            itinerary_id: Itinerary ID.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated PDF file.
        """
        itinerary = self.db_manager.get_itinerary(itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {itinerary_id} not found")

        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"itinerary_{itinerary_id}_{timestamp}.pdf"

        output_path = self.output_directory / filename

        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Itinerary for {itinerary.traveler_name}", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Destination: {itinerary.destination}", styles["Normal"]))
        story.append(Paragraph(f"Trip Dates: {itinerary.trip_start_date.date()} to {itinerary.trip_end_date.date()}", styles["Normal"]))

        with self.db_manager.get_session() as session:
            from src.database import FlightBooking, HotelBooking, ActivityBooking

            flights = (
                session.query(FlightBooking)
                .filter(FlightBooking.itinerary_id == itinerary_id)
                .all()
            )

            if flights:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Flights", styles["Heading2"]))
                for flight in flights:
                    story.append(
                        Paragraph(
                            f"{flight.airline} {flight.flight_number}: "
                            f"{flight.departure_airport} to {flight.arrival_airport}",
                            styles["Normal"],
                        )
                    )

        doc.build(story)

        logger.info(f"Generated PDF itinerary: {output_path}")
        return output_path

    def _generate_default_html(
        self, itinerary: Itinerary, flights: list, hotels: list, activities: list
    ) -> str:
        """Generate default HTML if template not found.

        Args:
            itinerary: Itinerary object.
            flights: List of flight bookings.
            hotels: List of hotel bookings.
            activities: List of activity bookings.

        Returns:
            HTML content string.
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Travel Itinerary - {itinerary.traveler_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4a90e2; color: white; }}
            </style>
        </head>
        <body>
            <h1>Travel Itinerary</h1>
            <p><strong>Traveler:</strong> {itinerary.traveler_name}</p>
            <p><strong>Destination:</strong> {itinerary.destination}</p>
            <p><strong>Trip Dates:</strong> {itinerary.trip_start_date.date()} to {itinerary.trip_end_date.date()}</p>
        """

        if flights:
            html += "<h2>Flights</h2><table><tr><th>Airline</th><th>Flight</th><th>Route</th><th>Departure</th></tr>"
            for flight in flights:
                html += f"<tr><td>{flight.airline}</td><td>{flight.flight_number}</td><td>{flight.departure_airport} to {flight.arrival_airport}</td><td>{flight.departure_time}</td></tr>"
            html += "</table>"

        if hotels:
            html += "<h2>Hotels</h2><table><tr><th>Hotel</th><th>Check-in</th><th>Check-out</th></tr>"
            for hotel in hotels:
                html += f"<tr><td>{hotel.hotel_name}</td><td>{hotel.check_in_date}</td><td>{hotel.check_out_date}</td></tr>"
            html += "</table>"

        html += "</body></html>"
        return html
