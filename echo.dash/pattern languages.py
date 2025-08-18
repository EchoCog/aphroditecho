# Define base class for a City Pattern Element.
class CityPattern:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def display(self):
        print(f"{self.name}: {self.description}")


# Define a pattern for a Main Street, the central hub for communication.
class MainStreet(CityPattern):
    def __init__(self, name="Main Street", description="Central communication hub"):
        super().__init__(name, description)
        self.connected_districts = []

    def add_district(self, district):
        self.connected_districts.append(district)
        print(f"Connected {district.name} to {self.name}")


# Define a pattern for a Public Square, a common meeting or innovation spot.
class PublicSquare(CityPattern):
    def __init__(self, name="Public Square", description="Shared space for innovation and strategic discussion"):
        super().__init__(name, description)

    def host_meeting(self):
        print(f"{self.name} is hosting a strategic meeting.")


# Define a pattern for a Neighborhood, representing clusters of departments.
class Neighborhood(CityPattern):
    def __init__(self, name, description="Cluster of related business units"):
        super().__init__(name, description)
        self.buildings = []

    def add_building(self, building):
        self.buildings.append(building)
        print(f"{building.name} added to {self.name}")


# Define a Building which can represent a team or a microservice with a specific function.
class Building(CityPattern):
    def __init__(self, name, description="Autonomous team or service"):
        super().__init__(name, description)


# Example Enterprise City Framework
class EnterpriseCity:
    def __init__(self):
        # The central communication backbone
        self.main_street = MainStreet()
        # Public square for innovation
        self.public_square = PublicSquare()
        # Create neighborhoods (business clusters)
        self.neighborhoods = []

    def add_neighborhood(self, neighborhood):
        self.neighborhoods.append(neighborhood)
        # Connect neighborhood to main street
        self.main_street.add_district(neighborhood)

    def display_city(self):
        print("Enterprise City Structure:")
        self.main_street.display()
        self.public_square.display()
        for n in self.neighborhoods:
            n.display()
            for b in n.buildings:
                b.display()


# Sample usage
def main():
    # Initialize the enterprise city
    city = EnterpriseCity()

    # Create neighborhoods representing different domains
    tech_district = Neighborhood("Tech District", "Focus on technology and product development")
    ops_district = Neighborhood("Operations District", "Handles operational and support functions")

    # Add buildings (teams/microservices) to neighborhoods
    tech_district.add_building(Building("Cloud Services", "Handles all cloud infrastructure"))
    tech_district.add_building(Building("Data Analytics", "Performs data analysis and reporting"))
    ops_district.add_building(Building("Customer Support", "Manages client relationships"))
    ops_district.add_building(Building("Logistics", "Oversees supply chain and distribution"))

    # Add neighborhoods to the enterprise city
    city.add_neighborhood(tech_district)
    city.add_neighborhood(ops_district)

    # Display the city structure
    city.display_city()

    # Host a meeting in the public square
    city.public_square.host_meeting()


if __name__ == "__main__":
    main()
