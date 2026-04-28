package com.ashwinmenon.www.calcounter.db;

import android.app.Application;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class DayRepository {
    private DayDao mDayDao;
    private List<Day> mAllDays;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    DayRepository(Application application) {
        AppDatabase db = AppDatabase.getDatabase(application);
        mDayDao = db.dayDao();
        mAllDays = mDayDao.getAll();
    }

    List<Day> getAllDays() {
        return mAllDays;
    }

    public void insert(Day day) {
        executor.execute(() -> mDayDao.insert(day));
    }

    public void shutdown() {
        executor.shutdown();
    }
}
