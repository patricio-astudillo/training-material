# Basics

This is a series of SQL commands that illustrate a number of basic
concepts of creating and accessing tables in a relational database.  If
you have SQLite around, it is easy to just read the SQL in, and
executing it in the database.

To follow along, start a new SQLite database:
```
$ sqlite3 test.db
```
The database will be stored in the `test.db` file, so that it can be
accessed later.

## What is it?

### Creating tables

Creating tables means defining columns, their data types, and
relations between them.  The relevant SQL statements are in
`create_tables.sql` that illustrates the `CREATE TABLE` statement:

```
sqlite> .read  create_tables.sql
```

This will create two tables, `persons` and `addresses`  Persons have
a first name, last name, and a reference to an address.  Addresses
are stored in the `addresses` table, and have a street, a number, and
a city.  It illustrates how to use primary/foreign keys.
Checking which tables are in the database is simple:

```
mysql> .tables
```

Checking on a table's schema can be done as well:
```
mysql> .schema persons
```


### Inserting data

Right now, the tables are empty, but they can be populated using the
`INSERT INTO` command, as illustrated in `insert_data.sql`.  Executing
it in SQLite:

```
sqlite> .read  insert_data.sql
```

To see the contents of the `persons` table, simply select all values:

```
sqlite> SELECT * FROM persons;
```


### Simple select data

To see all cities in the database, a `SELECT` statement can be executed:

```
sqlite> .read  distinct_cities.sql
```


### Joins

To find out who's actually living in London, the information in both
tables `persons` and `addresses` has to be combined using an `INNER JOIN`:

```
sqlite> .read  select_london_people.sql
```


### Inner joins, left joins

Illustrating joins in general, `inner_join.sql` and `left_join.sql`
can be used:

```
sqlite> .read  inner_join.sql
```

```
sqlite> .read  left_join.sql
```


### Altering tables

It is of course possible to modify table defintions, `add_age.sql`
illustrates this by adding a column `age` to the `persons` table
using `ALTER TABLE`:

```
sqlite> .read  add_age.sql
```

Adding the age of people requires `UPDATE`, which are also in
`add_age.sql`.
Looking at the `persons` table again, but using `LIMIt` to not see
all rows:

```
sqlite> SELECT * FROM persons LIMIT 2;
```


### Simple statistics

Computing trivial statistics is trivial, e.g., the average age of
people in the `persons` table can be done using the `AVG` function:

```
sqlite> .read average_age.sql
```


### More foreign keys

Making friends is easy as well, we create a table `friends` that
has a `person_id` and a `friend_id` column that represents a
friendship relation.  Both are foreign keys referencing `person_id`
in the `persons` table.

```
sqlite> .read make_friendships.sql
```

Note the `UNIQUE` constraint that ensures that people are only friends
once.


### More joins

Finding friends is now a maater of a join between three tables, or
rather, two, but the `persons` table is used twice:

```
sqlite> .read make_find_friendships.sql
```


### Transitive closure

To find friends of friends, one has to use a recursive query.  Note that
this can only be done in recent versions of SQLite.  The query in
`friends_of_friends.sql` will return all friends of the person with
liat name Fransen, as well as all their friends, and so on.

```
sqlite> .read friends_of_friends.sql
```


### Grouping

To count how many addresses we have in the `addresses` table for each
city, a `GROUP BY` can be used:

```
sqlite> .read count_address_by_city.sql
```

Results are shown ordered by count, descending.

Similarly, to count the persons in the `persons` table per city, we use
an `INNER JOIN` and a `GROUP BY`:

```
sqlite> .read how_many_person_per_city.sql~
```
