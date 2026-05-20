# CalCounter

A simple Android calorie counter app built with Java and Room database.

## Features

- **Daily calorie & protein tracking** — log food entries with calorie and protein values for each day
- **Calorie-to-protein ratio** — see your ratio at a glance to help balance macros
- **Trend chart** — view a rolling average of calorie intake over configurable time windows (powered by MPAndroidChart)
- **Configurable settings** — adjust how many days to query and the averaging window
- **Persistent storage** — all data stored locally with Room (SQLite) so nothing is lost between sessions

## Screenshots

_Coming soon._

## Tech Stack

| Component | Library |
|-----------|---------|
| Language | Java 8 |
| Database | AndroidX Room 2.0 |
| Charts | [MPAndroidChart](https://github.com/PhilJay/MPAndroidChart) v3.1.0 |
| Boilerplate reduction | [Lombok](https://projectlombok.org/) 1.18.12 |
| Min SDK | 27 (Android 8.1) |
| Target SDK | 30 (Android 11) |
| Build system | Gradle 6.5 / AGP 4.1.1 |

## Project Structure

```
app/src/main/java/com/ashwinmenon/www/calcounter/
├── MainActivity.java          # Host activity, navigation between fragments
├── MainActivityFragment.java  # Main screen — list of days with calorie/protein totals
├── FoodFragment.java          # Add/view food entries for a selected day
├── ChartFragment.java         # Line chart showing calorie trend
├── SettingsFragment.java      # User preferences (days to query, averaging window)
├── DayAdapter.java            # RecyclerView adapter for day list
├── FoodAdapter.java           # RecyclerView adapter for food list
└── db/
    ├── AppDatabase.java       # Room database singleton
    ├── Day.java               # Day entity
    ├── DayDao.java            # DAO for Day queries
    ├── DayRepository.java     # Repository layer for Day
    ├── Food.java              # Food entity (name, calories, proteins, dayId)
    └── FoodDao.java           # DAO for Food queries
```

## Getting Started

### Prerequisites

- [Android Studio](https://developer.android.com/studio) (Arctic Fox or later recommended)
- JDK 8+
- An Android device or emulator running API 27+

### Build & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/IngridMorstrad/CalCounter.git
   ```
2. Open the project in Android Studio.
3. Let Gradle sync complete.
4. Run the app on an emulator or connected device (API 27+).

## Usage

1. The main screen shows a list of days from a start date to today.
2. Tap a day to add food entries (name, calories, proteins).
3. The top bar displays total calories, proteins, and the calorie-to-protein ratio for the configured window.
4. Tap the calorie total to toggle between cumulative and daily average view.
5. Use the **View Trend** menu option to see a line chart of your calorie intake averaged over a configurable number of days.
6. Adjust the query window and averaging period in **Settings**.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project does not currently specify a license. Please contact the author before reusing the code.