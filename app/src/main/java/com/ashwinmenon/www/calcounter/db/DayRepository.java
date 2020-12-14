package com.ashwinmenon.www.calcounter.db;

import android.app.Application;
import android.os.AsyncTask;

import java.util.List;

public class DayRepository {
    private DayDao mDayDao;
    private List<Day> mAllDays;

    DayRepository(Application application) {
        AppDatabase db = AppDatabase.getDatabase(application);
        mDayDao = db.dayDao();
        mAllDays = mDayDao.getAll();
    }

    List<Day> getAllDays() {
        return mAllDays;
    }

    public void insert (Day word) {
        new insertAsyncTask(mDayDao).execute(word);
    }

    private static class insertAsyncTask extends AsyncTask<Day, Void, Void> {

        private DayDao mAsyncTaskDao;

        insertAsyncTask(DayDao dao) {
            mAsyncTaskDao = dao;
        }

        @Override
        protected Void doInBackground(final Day... params) {
            mAsyncTaskDao.insert(params[0]);
            return null;
        }
    }
}

