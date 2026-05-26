# CalCounter

A lightweight Android app for tracking your daily calorie intake.

## Features

- **Daily Calorie Tracking** - Log food entries throughout the day and monitor your total calorie consumption
- **Food Management** - Add, edit, and organize food items with calorie information
- **Visual Charts** - View your calorie history over time with interactive charts powered by MPAndroidChart
- **Configurable Settings** - Customize the app to match your dietary goals and preferences

## Prerequisites

- [Android Studio](https://developer.android.com/studio) (4.1 or later recommended)
- Android SDK with API level 30 (Android 11)
- JDK 8 or later
- Minimum device/emulator running Android 8.1 (API 27)

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/IngridMorstrad/CalCounter.git
   cd CalCounter
   ```

2. **Open in Android Studio**

   Open Android Studio and select **File > Open**, then navigate to the cloned project directory.

3. **Build the project**

   Using the Gradle wrapper from the command line:

   ```bash
   ./gradlew assembleDebug
   ```

   Or use **Build > Make Project** in Android Studio.

4. **Run on a device or emulator**

   Connect an Android device (API 27+) or start an emulator, then run:

   ```bash
   ./gradlew installDebug
   ```

   Or use **Run > Run 'app'** in Android Studio.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Java 8 |
| Database | Android Room (SQLite) |
| Charts | MPAndroidChart v3.1.0 |
| Build System | Gradle 4.1.1 (Android Plugin) |
| Architecture | Fragments + Repository Pattern |
| Utilities | Lombok, Commons IO |

## Project Structure

```
app/src/main/java/com/ashwinmenon/www/calcounter/
├── MainActivity.java          # Main entry point
├── MainActivityFragment.java  # Daily overview fragment
├── FoodFragment.java          # Food entry management
├── ChartFragment.java         # Calorie chart visualization
├── SettingsFragment.java      # App preferences
├── DayAdapter.java            # RecyclerView adapter for days
├── FoodAdapter.java           # RecyclerView adapter for foods
└── db/
    ├── AppDatabase.java       # Room database definition
    ├── Day.java               # Day entity
    ├── DayDao.java            # Day data access object
    ├── DayRepository.java     # Repository for day operations
    ├── Food.java              # Food entity
    └── FoodDao.java           # Food data access object
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## Sponsor

If you find this project useful, consider [sponsoring the developer on GitHub](https://github.com/sponsors/IngridMorstrad).
