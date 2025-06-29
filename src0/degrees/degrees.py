import csv
import sys

from util import Node, QueueFrontier


# Maps names to a set of corresponding person_ids
names = {}

# Maps person_ids to a dictionary of: name, birth, movies (a set of movie_ids)
people = {}

# Maps movie_ids to a dictionary of: title, year, stars (a set of person_ids)
movies = {}


def load_data(directory):
    """
    Load data from CSV files into memory.
    """
    # Load people
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set(),
            }
            if row["name"].lower() not in names:
                names[row["name"].lower()] = {row["id"]}
            else:
                names[row["name"].lower()].add(row["id"])

    # Load movies
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set(),
            }

    # Load stars
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                pass


def main():
    if len(sys.argv) > 2:
        sys.exit("Usage: python degrees.py [directory]")
    directory = sys.argv[1] if len(sys.argv) == 2 else "large"

    print("DEBUG: Running main(), directory =", directory)  # ✅ valid now

    # Load data from files into memory
    print("Loading data...")
    load_data(directory)
    print("Data loaded.")

    source = person_id_for_name(input("Name: "))
    if source is None:
        sys.exit("Person not found.")
    target = person_id_for_name(input("Name: "))
    if target is None:
        sys.exit("Person not found.")

    path = shortest_path(source, target)

    if path is None:
        print("Not connected.")
    else:
        degrees = len(path)
        print(f"{degrees} degrees of separation.")
        path = [(None, source)] + path
        for i in range(degrees):
            person1 = people[path[i][1]]["name"]
            person2 = people[path[i + 1][1]]["name"]
            movie = movies[path[i + 1][0]]["title"]
            print(f"{i + 1}: {person1} and {person2} starred in {movie}")


def dump_frontier(frontier):
    """
    Debugging function to dump the contents of the frontier.
    """
    print("Frontier contents:")
    for node in frontier.frontier:
        if node.action is not None and node.state is not None:
            print(
                f"Frontier: Actor: {people[node.state]['name']} id: {node.state}, Movie: {movies[node.action]['title']}, id: {node.action}, Parent: {people[node.parent.state]['name'] if node.parent else None}"
            )


def shortest_path(source, target):
    """
    For each person, get the neighbors of that person if not target in one, push those neighbors
    onto the frontier  and then explore the neighbors of those neighbors until the target is found.

    Neighbors is pairs of (movie_id, person_id) and are really only used to traverse through to
    related people, but because UX wants to know the movies that connect them, we keep track of
    the movie_id as well. When every we process any person, we can find all people that
    they are related to through the movies and thus there is no point in trying to process
    that person again once they have been explored. Put diffeently, we should never need to
    call neighbors_for_person on a person that has already been explored. To optimize this, we
    will keep track of explored people in a set.

    Put differently, each state A is a set of people in a movie and each edge is to another movie B if
    one or more people in set A acted in that movie because that allows us to traverse to that
    state. In essence each Action is a movie from one state to another.
    Transitioning to a state means that we can find all the people in that movie and then
    explore those people to see if they are the target person.

    Essentially, start with the movies that the source person has starred in. The neighbors_for_person function
    will return a set of (movie_id, person_id) pairs for people who starred with the source person.
    If the target person is in those movies, then we can return the path

    The neighbors of those movies
    If the target person is not in those movies, then explore the neighbors of those movies.
    The neighbors are the movies that other people have starred in with the source person.
    If the target person is not found, then continue to explore the neighbors of those movies
    until the target person is found.
    """
    path = []
    if source == target:
        return path;

    
    if not people[source]["movies"]:
        raise Exception("source has no movies")

    # Keep track of number of states explored
    explored_people = set()
    explored_movies = set()

    start = source

    # Initialize frontier to just the starting position
    start = Node(state=start, parent=None, action=None)
    frontier = QueueFrontier()
    frontier.add(start)

    # Keep looping until solution found
    while True:
        # dump_frontier(frontier)  # Debugging line to see frontier contents
        # On the frontier we have people who are 1 degree from the source and then 2 ...
        # If nothing left in frontier, then no path
        if frontier.empty():
            return None

        # Choose a node from the frontier
        node = frontier.remove()
        actor = node.state
        movie = node.action
        if actor in explored_people and (movie is None or movie in explored_movies):
            # If we have already explored this person and movie, then skip
            continue

        explored_people.add(actor)
        if movie is not None:
            explored_movies.add(movie)

        # IF the target is in this movie, then we can return the path
        if movie is not None:
            if target in movies[movie]["stars"]:
                # If we found the target, we can return the path
                path = []
                while node is not None:
                    path.append((node.action, node.state))
                    node = node.parent
                path.reverse()
                return path

        # if the target is acting with the person we are exploring, then we can return the path
        people_acting_with_source = neighbors_for_person(actor)
        if target in [person for movie, person in people_acting_with_source]:
            # If the target is in the neighbors of the source, then we can return the path
            path = []
            for movie, person in people_acting_with_source:
                if person == target:
                    path.append((movie, person))
                    break
            while node is not None:
                if node.action is not None:
                    path.append((node.action, node.state))
                node = node.parent
            path.reverse()
            return path

        # If here we have not found the target in this node.
        for movie, person in people_acting_with_source:
            child = Node(state=person, parent=node, action=movie)
            if (
                person not in explored_people
                and movie not in explored_movies
                and not frontier.contains_state(person)
            ):
                frontier.add(child)

    raise NotImplementedError


def person_id_for_name(name):
    """
    Returns the IMDB id for a person's name,
    resolving ambiguities as needed.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        return None
    elif len(person_ids) > 1:
        print(f"Which '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            name = person["name"]
            birth = person["birth"]
            print(f"ID: {person_id}, Name: {name}, Birth: {birth}")
        try:
            person_id = input("Intended Person ID: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


# All people who acted in a movie with a given person
def neighbors_for_person(person_id):
    """
    Returns (movie_id, person_id) pairs for people
    who starred with a given person.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for person_id in movies[movie_id]["stars"]:
            neighbors.add((movie_id, person_id))

    return neighbors


if __name__ == "__main__":
    main()
