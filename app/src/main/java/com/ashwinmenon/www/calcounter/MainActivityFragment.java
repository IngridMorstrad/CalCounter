package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import android.app.Fragment;
import android.os.Bundle;
import android.preference.PreferenceManager;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.TextView;

import com.ashwinmenon.www.calcounter.db.AppDatabase;
import com.ashwinmenon.www.calcounter.db.Day;
import com.ashwinmenon.www.calcounter.db.DayDao;
import com.ashwinmenon.www.calcounter.db.Food;
import com.ashwinmenon.www.calcounter.db.FoodDao;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Main fragment that displays list of dates.
 */
public class MainActivityFragment extends Fragment {

    // TODO: Refactor to use food file or a database
    // TODO: USDA Food API
    // TODO: Ability to add multiple of same food
    // TODO: Add sort by cals/proteins/ratio & asc/desc
    // TODO: Add option to colour foodsForAllDays by ratio/calorie/protein
    static int daysToQuery;
    static boolean displayNutritionAverages;
    static List<List<Food>> foodsForAllDays = new ArrayList<>();
    private ArrayAdapter<Day> daysAdapter;
    private ListView lvItems;
    private OnDaySelectedListener mCallback;
    static List<Day> days = new ArrayList<>();

    @Override
    public void onCreate(Bundle savedInstanceState) {
        SimpleDateFormat dateFormatter = new SimpleDateFormat("dd/MM/yyyy");
        Date startDay, currDay;
        GregorianCalendar gregorianCalendar;

        try {
            String startDate = "13/10/2020";
            startDay = dateFormatter.parse(startDate);
        } catch (ParseException e) {
            throw new RuntimeException(e);
        }

        try {
            currDay = dateFormatter.parse(dateFormatter.format(Calendar.getInstance().getTime()));
        } catch (ParseException e) {
            throw new RuntimeException(e);
        }

        gregorianCalendar = new GregorianCalendar();

        for (gregorianCalendar.setTime(startDay); !gregorianCalendar.getTime().after(currDay); gregorianCalendar.add(Calendar.DATE, 1)) {
            Date time = gregorianCalendar.getTime();
            int currentTime = (int) (time.getTime() / 1000);
            Day day = new Day(currentTime, dateFormatter.format(gregorianCalendar.getTime()));
            days.add(day);
        }

        AppDatabase db = AppDatabase.getDatabase(getActivity().getApplicationContext());
        DayDao dayDao = db.dayDao();
        FoodDao foodDao = db.foodDao();
        foodsForAllDays = new ArrayList<>();
        new Thread(() -> {
            List<Day> daysInDB = dayDao.getAll();
            Set<Integer> dayIDsInDB = new HashSet<>();
            for (Day dayInDB : daysInDB) {
                dayIDsInDB.add(dayInDB.dayId);
            }
            List<Day> missingDays = new ArrayList<>();
            for (Day day : days) {
                if (!dayIDsInDB.contains(day.dayId)) {
                    missingDays.add(day);
                }
            }
            dayDao.insertAll(missingDays.toArray(new Day[0]));
            List<Food> foods = foodDao.getAll();
            Log.v("MAF", "Food size: " + foods.size());
            for (Food f : foods) {
                Log.v("MAF", "Foods are: " + f.getName());
            }
            for (Day day : days) {
                Log.v("MainActivityFragment", "Day ID is: " + day.getDayId());
                foodsForAllDays.add(foodDao.loadAllByDayId(day.getDayId()));
            }
        }).start();

        displayNutritionAverages = false;

        new Thread(() -> {
            Log.v("MainActivityFragment", "food dao is: " + foodDao.getAll());
        }).start();
        daysAdapter = new DayAdapter(getActivity(), days);

        super.onCreate(savedInstanceState);
    }

    public interface OnDaySelectedListener {
        void onDaySelected(int dayPosition);
    }

    @Override
    public void onAttach(Activity activity) {
        super.onAttach(activity);

        // This makes sure that the container activity has implemented
        // the callback interface. If not, it throws an exception
        try {
            mCallback = ((OnDaySelectedListener) activity);
        } catch (ClassCastException e) {
            throw new ClassCastException(activity.toString()
                    + " must implement OnDaySelectedListener");
        }
    }

    // Add an ItemClickListener to start an activity where we can add foodsForAllDays for the day clicked
    private void setupListViewListener() {
        lvItems.setOnItemClickListener(
                (parent, view, position, id) -> {
                    mCallback.onDaySelected(days.size() - 1 - position);
                });
    }

    private void updateDisplay() {
        Activity activity = getActivity();
        TextView proteinsView = activity.findViewById(R.id.proteins);
        TextView calsView = activity.findViewById(R.id.calories);
        TextView ratioView = activity.findViewById(R.id.avg);
        int proteinSum = 0, calSum = 0;
        double ratio = 0.0;

        for (int day = Math.max(0, foodsForAllDays.size() - daysToQuery); day < foodsForAllDays.size(); day++) {
            for (Food food : foodsForAllDays.get(day)) {
                proteinSum += food.getProteins();
                calSum += food.getCalories();
            }
        }

        if (displayNutritionAverages) {
            proteinsView.setText(String.format("%.2f", (double) proteinSum / daysToQuery));
            calsView.setText(String.format("%.2f", (double) calSum / daysToQuery));
        } else {
            proteinsView.setText(String.valueOf(proteinSum));
            calsView.setText(String.valueOf(calSum));
        }

        if (proteinSum != 0) {
            ratio = (double) calSum / proteinSum;
        }

        ratioView.setText(String.format("%.2f", ratio));
        daysAdapter.notifyDataSetChanged();
    }

    @Override
    public void onResume() {
        super.onResume();

        daysToQuery = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(getActivity()).getString(getActivity().getString(R.string.key_days), "7"));
        updateDisplay();

        FoodDao foodDao = AppDatabase.getDatabase(getActivity().getApplicationContext()).foodDao();
        int dayIndex = 0;
        for (List<Food> foodForDay : foodsForAllDays) {
            for (Food food : foodForDay) {
                final String foodName = food.getName();
                final int foodCals = food.getCalories();
                final int foodProteins = food.getProteins();
                final int dayId = days.get(dayIndex).getDayId();
                final Food newFood = new Food(foodName, foodCals, foodProteins, dayId);
                new Thread(() -> foodDao.updateAll(newFood)).start();
            }
            dayIndex++;
        }

    }

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.fragment_main, container, false);

        lvItems = rootView.findViewById(R.id.lvItems);

        lvItems.setAdapter(daysAdapter);

        View cals = rootView.findViewById(R.id.calories);

        cals.setOnClickListener(v -> {
            displayNutritionAverages = !displayNutritionAverages;
            updateDisplay();
        });

        setupListViewListener();

        return rootView;
    }
}
