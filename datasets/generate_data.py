import csv
import random
from datetime import date, timedelta

random.seed(42)

CATEGORIES = ["Fiction", "Non-Fiction", "Science", "Technology", "History",
              "Biography", "Self-Help", "Mystery", "Romance", "Children's"]

BOOKS_DATA = [
    # Fiction
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", "978-0-7432-7356-5", 1925),
    ("To Kill a Mockingbird", "Harper Lee", "Fiction", "978-0-06-112008-4", 1960),
    ("1984", "George Orwell", "Fiction", "978-0-452-28423-4", 1949),
    ("Pride and Prejudice", "Jane Austen", "Fiction", "978-0-14-143951-8", 1813),
    ("The Catcher in the Rye", "J.D. Salinger", "Fiction", "978-0-316-76948-0", 1951),
    ("Brave New World", "Aldous Huxley", "Fiction", "978-0-06-085052-4", 1932),
    ("The Alchemist", "Paulo Coelho", "Fiction", "978-0-06-112241-5", 1988),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fiction", "978-0-439-70818-8", 1997),
    ("The Lord of the Rings", "J.R.R. Tolkien", "Fiction", "978-0-618-00222-5", 1954),
    ("Animal Farm", "George Orwell", "Fiction", "978-0-452-28424-1", 1945),
    # Non-Fiction
    ("Sapiens", "Yuval Noah Harari", "Non-Fiction", "978-0-06-231609-7", 2011),
    ("Educated", "Tara Westover", "Non-Fiction", "978-0-399-59050-4", 2018),
    ("The Immortal Life of Henrietta Lacks", "Rebecca Skloot", "Non-Fiction", "978-1-4000-5217-2", 2010),
    ("Into the Wild", "Jon Krakauer", "Non-Fiction", "978-0-385-48680-4", 1996),
    ("Fast Food Nation", "Eric Schlosser", "Non-Fiction", "978-0-618-13101-7", 2001),
    ("The Devil in the White City", "Erik Larson", "Non-Fiction", "978-0-375-72560-7", 2003),
    ("Unbroken", "Laura Hillenbrand", "Non-Fiction", "978-0-8129-7095-0", 2010),
    ("The Glass Castle", "Jeannette Walls", "Non-Fiction", "978-0-7432-7136-3", 2005),
    ("Born a Crime", "Trevor Noah", "Non-Fiction", "978-0-385-54132-6", 2016),
    ("I Am Malala", "Malala Yousafzai", "Non-Fiction", "978-0-316-32241-6", 2013),
    # Science
    ("A Brief History of Time", "Stephen Hawking", "Science", "978-0-553-38016-3", 1988),
    ("The Selfish Gene", "Richard Dawkins", "Science", "978-0-19-929115-1", 1976),
    ("Cosmos", "Carl Sagan", "Science", "978-0-345-53943-4", 1980),
    ("The Origin of Species", "Charles Darwin", "Science", "978-0-14-043205-3", 1859),
    ("The Double Helix", "James Watson", "Science", "978-0-7432-1630-1", 1968),
    ("Astrophysics for People in a Hurry", "Neil deGrasse Tyson", "Science", "978-0-393-60939-4", 2017),
    ("The Gene", "Siddhartha Mukherjee", "Science", "978-1-4767-3350-8", 2016),
    ("Seven Brief Lessons on Physics", "Carlo Rovelli", "Science", "978-0-399-18441-3", 2014),
    ("The Elegant Universe", "Brian Greene", "Science", "978-0-393-33810-5", 1999),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "Science", "978-0-374-53355-7", 2011),
    # Technology
    ("Clean Code", "Robert C. Martin", "Technology", "978-0-13-235088-4", 2008),
    ("The Pragmatic Programmer", "David Thomas", "Technology", "978-0-13-595705-9", 1999),
    ("Design Patterns", "Gang of Four", "Technology", "978-0-201-63361-0", 1994),
    ("Introduction to Algorithms", "Thomas H. Cormen", "Technology", "978-0-262-03384-8", 1990),
    ("The Mythical Man-Month", "Frederick P. Brooks", "Technology", "978-0-201-83595-3", 1975),
    ("Code Complete", "Steve McConnell", "Technology", "978-0-7356-1967-8", 2004),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "Technology", "978-0-13-604259-4", 1994),
    ("Deep Learning", "Ian Goodfellow", "Technology", "978-0-262-03561-3", 2016),
    ("Python Crash Course", "Eric Matthes", "Technology", "978-1-59327-928-8", 2015),
    ("The Innovators", "Walter Isaacson", "Technology", "978-1-4767-0869-8", 2014),
    # History
    ("Guns, Germs, and Steel", "Jared Diamond", "History", "978-0-393-31755-8", 1997),
    ("The Rise and Fall of the Third Reich", "William L. Shirer", "History", "978-0-671-72868-7", 1960),
    ("Alexander the Great", "Robin Lane Fox", "History", "978-0-14-303823-3", 1973),
    ("A People's History of the United States", "Howard Zinn", "History", "978-0-06-083865-2", 1980),
    ("The Silk Roads", "Peter Frankopan", "History", "978-1-101-91218-3", 2015),
    # Biography
    ("Steve Jobs", "Walter Isaacson", "Biography", "978-1-4516-4853-9", 2011),
    ("Leonardo da Vinci", "Walter Isaacson", "Biography", "978-1-5011-3915-4", 2017),
    ("Long Walk to Freedom", "Nelson Mandela", "Biography", "978-0-316-54818-3", 1994),
    ("The Diary of a Young Girl", "Anne Frank", "Biography", "978-0-553-57712-5", 1947),
    ("Einstein: His Life and Universe", "Walter Isaacson", "Biography", "978-0-7432-6473-0", 2007),
    # Self-Help
    ("Atomic Habits", "James Clear", "Self-Help", "978-0-7352-1129-7", 2018),
    ("The 7 Habits of Highly Effective People", "Stephen R. Covey", "Self-Help", "978-0-7432-6951-3", 1989),
    ("How to Win Friends and Influence People", "Dale Carnegie", "Self-Help", "978-0-671-02703-5", 1936),
    ("Think and Grow Rich", "Napoleon Hill", "Self-Help", "978-1-59330-200-5", 1937),
    ("The Power of Now", "Eckhart Tolle", "Self-Help", "978-1-57731-480-6", 1997),
    # Mystery
    ("And Then There Were None", "Agatha Christie", "Mystery", "978-0-06-207348-8", 1939),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson", "Mystery", "978-0-307-45454-1", 2005),
    ("Gone Girl", "Gillian Flynn", "Mystery", "978-0-307-58836-4", 2012),
    ("In the Woods", "Tana French", "Mystery", "978-0-670-03862-5", 2007),
    ("The Da Vinci Code", "Dan Brown", "Mystery", "978-0-307-47427-3", 2003),
    # Romance
    ("Outlander", "Diana Gabaldon", "Romance", "978-0-440-21256-1", 1991),
    ("Me Before You", "Jojo Moyes", "Romance", "978-0-14-312454-9", 2012),
    ("The Notebook", "Nicholas Sparks", "Romance", "978-0-446-60523-4", 1996),
    ("It Ends with Us", "Colleen Hoover", "Romance", "978-1-5011-1534-9", 2016),
    ("The Hating Game", "Sally Thorne", "Romance", "978-0-06-247089-4", 2016),
    # Children's
    ("Charlotte's Web", "E.B. White", "Children's", "978-0-06-440055-8", 1952),
    ("The Very Hungry Caterpillar", "Eric Carle", "Children's", "978-0-399-20853-6", 1969),
    ("Where the Wild Things Are", "Maurice Sendak", "Children's", "978-0-06-443001-6", 1963),
    ("The Lion, the Witch and the Wardrobe", "C.S. Lewis", "Children's", "978-0-06-447104-7", 1950),
    ("Matilda", "Roald Dahl", "Children's", "978-0-14-241037-1", 1988),
]

FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry",
               "Iris", "James", "Karen", "Liam", "Mia", "Noah", "Olivia", "Paul",
               "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
               "Yara", "Zach", "Amy", "Brian", "Claire", "Derek", "Elena", "Felix",
               "Gina", "Hugo", "Ivy", "Jack", "Kelly", "Leo", "Maya", "Nate",
               "Ora", "Pete", "Rita", "Sean", "Tara", "Ulrich", "Vera", "Wade",
               "Xena", "Yusuf"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White",
              "Harris", "Martin", "Thompson", "Moore", "Young", "Allen", "King",
              "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter",
              "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell",
              "Parker", "Evans", "Edwards", "Collins", "Stewart", "Sanchez",
              "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell", "Murphy",
              "Bailey", "Rivera", "Cooper"]

MEMBERSHIP_TYPES = ["basic", "premium", "student"]

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

BASE_DATE = date(2024, 1, 1)
TODAY = date(2026, 5, 21)

# Generate books.csv
with open("books.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["book_id", "title", "author", "category", "isbn",
                     "publication_year", "total_copies", "available_copies"])
    for i, (title, author, category, isbn, year) in enumerate(BOOKS_DATA, 1):
        total = random.randint(2, 8)
        available = random.randint(0, total)
        writer.writerow([i, title, author, category, isbn, year, total, available])

print(f"books.csv: {len(BOOKS_DATA)} records")

# Generate borrowers.csv (60 borrowers)
borrowers = []
emails_used = set()
with open("borrowers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["borrower_id", "name", "email", "phone", "membership_date",
                     "membership_type", "address"])
    for i in range(1, 61):
        fn = FIRST_NAMES[i - 1] if i <= len(FIRST_NAMES) else f"User{i}"
        ln = LAST_NAMES[i - 1] if i <= len(LAST_NAMES) else f"Name{i}"
        name = f"{fn} {ln}"
        base_email = f"{fn.lower()}.{ln.lower()}@example.com"
        email = base_email
        counter = 1
        while email in emails_used:
            email = f"{fn.lower()}.{ln.lower()}{counter}@example.com"
            counter += 1
        emails_used.add(email)
        phone = f"+1-555-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        mem_date = random_date(date(2022, 1, 1), date(2025, 12, 31))
        mem_type = random.choice(MEMBERSHIP_TYPES)
        address = f"{random.randint(100, 999)} Main St, City {random.randint(1, 50)}"
        borrowers.append(i)
        writer.writerow([i, name, email, phone, mem_date, mem_type, address])

print(f"borrowers.csv: 60 records")

# Generate transactions.csv (200 transactions)
num_books = len(BOOKS_DATA)
num_borrowers = 60
transactions_count = 0

with open("transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["transaction_id", "book_id", "borrower_id", "borrow_date",
                     "due_date", "return_date", "status", "fine_amount"])
    for tid in range(1, 221):
        book_id = random.randint(1, num_books)
        borrower_id = random.randint(1, num_borrowers)
        borrow_date = random_date(BASE_DATE, date(2026, 4, 30))
        due_date = borrow_date + timedelta(days=14)

        # Determine status
        r = random.random()
        if r < 0.60:  # returned on time
            return_date = random_date(borrow_date, due_date)
            status = "returned"
            fine_amount = 0.0
        elif r < 0.80:  # overdue (not returned)
            if due_date < TODAY:
                return_date = ""
                status = "overdue"
                days_overdue = (TODAY - due_date).days
                fine_amount = round(days_overdue * 0.50, 2)
            else:
                return_date = ""
                status = "active"
                fine_amount = 0.0
        elif r < 0.92:  # returned late
            late_days = random.randint(1, 30)
            return_date = due_date + timedelta(days=late_days)
            if return_date > TODAY:
                return_date = ""
                status = "overdue" if due_date < TODAY else "active"
                fine_amount = round((TODAY - due_date).days * 0.50, 2) if due_date < TODAY else 0.0
            else:
                status = "returned"
                fine_amount = round(late_days * 0.50, 2)
        else:  # active (currently borrowed)
            return_date = ""
            status = "active" if due_date >= TODAY else "overdue"
            fine_amount = round((TODAY - due_date).days * 0.50, 2) if due_date < TODAY else 0.0

        writer.writerow([tid, book_id, borrower_id, borrow_date, due_date,
                         return_date, status, fine_amount])
        transactions_count += 1

print(f"transactions.csv: {transactions_count} records")
print("Dataset generation complete!")
