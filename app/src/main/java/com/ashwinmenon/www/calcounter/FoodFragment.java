package com.ashwinmenon.www.calcounter;

import android.app.Fragment;
import android.os.Bundle;
import androidx.annotation.Nullable;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.ashwinmenon.www.calcounter.db.AppDatabase;
import com.ashwinmenon.www.calcounter.db.Food;
import com.ashwinmenon.www.calcounter.db.FoodDao;

import java.util.List;

import lombok.NonNull;

public class FoodFragment extends Fragment {

    public static final String POSITION_KEY = "com.ashwinmenon.www.calcounter.POSITION";
    private ArrayAdapter <Food> dailyFoodAdapter;
    private int proteinSum;
    private int calsSum;
    private List<Food> foodsForTheDay;
    private int position;

    public void updatePosition(int position) {
        this.position = position;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Bundle bundle = this.getArguments();
        if (bundle != null) {
            position = bundle.getInt(POSITION_KEY, -1);
        }
        if (position == -1) {
            Toast T = Toast.makeText(getActivity(), "POSITION ERROR", Toast.LENGTH_LONG);
            T.show();
            return;
        }

        foodsForTheDay = MainActivityFragment.foodsForAllDays.get(position);
        proteinSum = 0;
        calsSum = 0;

        for (Food food: foodsForTheDay) {
            proteinSum += food.getProteins();
            calsSum += food.getCalories();
        }

        dailyFoodAdapter = new FoodAdapter(getActivity(), foodsForTheDay);
    }

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.fragment_food, container, false);

        AdapterView.OnItemLongClickListener deleteItem = (parent, view, position, id) -> {
            calsSum -= foodsForTheDay.get(position).getCalories();
            proteinSum -= foodsForTheDay.get(position).getProteins();

            // Refresh the adapter
            dailyFoodAdapter.remove(foodsForTheDay.get(position));
            updateDailyViews(rootView);

            // Return true consumes the long click event (marks it handled)
            return true;
        };

        ListView lvFoods = rootView.findViewById(R.id.lvFoods);
        lvFoods.setAdapter(dailyFoodAdapter);
        lvFoods.setOnItemLongClickListener(deleteItem);

        Button addFood = rootView.findViewById(R.id.btnAdd);
        addFood.setOnClickListener(
                v -> {
                    EditText etFood = rootView.findViewById(R.id.etFood);
                    String foodName = etFood.getText().toString();

                    EditText etProteins = rootView.findViewById(R.id.etProteins);
                    int proteins = Integer.parseInt(etProteins.getText().toString());
                    proteinSum += proteins;

                    EditText etCals = rootView.findViewById(R.id.etCals);
                    int cals = Integer.parseInt(etCals.getText().toString());
                    calsSum += cals;

                    etCals.setText("");
                    etProteins.setText("");
                    etFood.setText("");

                    Log.v("FoodFragment", "Day id is: " + MainActivityFragment.days.get(position).getDayId());
                    Food newFood = new Food(foodName, cals, proteins, MainActivityFragment.days.get(position).getDayId());
                    dailyFoodAdapter.add(newFood);

                    AppDatabase db = AppDatabase.getDatabase(getActivity().getApplicationContext());
                    // DayDao dayDao = db.dayDao();
                    FoodDao foodDao = db.foodDao();
                    Thread t = new Thread(() -> {
                        /*
                        List<Day> myDays = dayDao.getAll();
                        for (Day d : myDays) {
                            Log.v("FF", "days are: " + d.getDay_id());
                        }
                        */
                        foodDao.insertAll(newFood);
                        List<Food> fods = foodDao.getAll();
                        Log.v("FF", "Food size is: " + fods.size());
                    });
                    t.start();


                    updateDailyViews(rootView);
                }
        );

        updateDailyViews(rootView);

        return rootView;
    }

    private void updateDailyViews(View rootView) {
        TextView dailyCalSum = rootView.findViewById(R.id.tvDailyCals);
        TextView dailyProteinSum = rootView.findViewById(R.id.tvDailyProteins);
        TextView avgView = rootView.findViewById(R.id.tvDailyAverage);

        dailyCalSum.setText(String.valueOf(calsSum));
        dailyProteinSum.setText(String.valueOf(proteinSum));
        avgView.setText(String.format("%.2f", calcAverage(calsSum, proteinSum)));
    }

    private double calcAverage(int calsSum, int proteinSum) {
        if (proteinSum == 0) return -1.0;
        return (double)calsSum/proteinSum;
    }
}
