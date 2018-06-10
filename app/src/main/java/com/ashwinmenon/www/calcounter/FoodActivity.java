package com.ashwinmenon.www.calcounter;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;

public class FoodActivity extends AppCompatActivity {

    private ArrayAdapter <Food> dailyFoodAdapter;
    private Integer proteinSum;
    private Integer calsSum;
    private List<Food> foodsForTheDay;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_food);
        Intent intent = getIntent();

        Integer pos = intent.getIntExtra(MainActivityFragment.POSITION, -1);
        if (pos == -1) {
            Toast T = Toast.makeText(this, "POSITION ERROR", Toast.LENGTH_LONG);
            T.show();
            return;
        }

        foodsForTheDay = MainActivityFragment.foods.get(pos);
        proteinSum = 0;
        calsSum = 0;

        for (Food food: foodsForTheDay) {
            proteinSum += food.getProteinsInt();
            calsSum += food.getCaloriesInt();
        }

        dailyFoodAdapter = new FoodAdapter(this, MainActivityFragment.foods.get(pos));

        Button addFood = findViewById(R.id.btnAdd);

        AdapterView.OnItemLongClickListener deleteItem = (parent, view, position, id) -> {
            calsSum -= foodsForTheDay.get(position).getCaloriesInt();
            proteinSum -= foodsForTheDay.get(position).getProteinsInt();

            // Refresh the adapter
            dailyFoodAdapter.remove(foodsForTheDay.get(position));
            updateDailyViews();

            // Return true consumes the long click event (marks it handled)
            return true;
        };

        ListView lvFoods = findViewById(R.id.lvFoods);
        lvFoods.setAdapter(dailyFoodAdapter);
        lvFoods.setOnItemLongClickListener(deleteItem);

        addFood.setOnClickListener(
                v -> {
                    EditText etFood = (EditText)findViewById(R.id.etFood);
                    String foodName = etFood.getText().toString();

                    EditText etProteins = (EditText) findViewById(R.id.etProteins);
                    Integer proteins = Integer.parseInt(etProteins.getText().toString());
                    proteinSum += proteins;

                    EditText etCals = (EditText) findViewById(R.id.etCals);
                    Integer cals = Integer.parseInt(etCals.getText().toString());
                    calsSum += cals;

                    etCals.setText("");
                    etProteins.setText("");
                    etFood.setText("");

                    dailyFoodAdapter.add(new Food(foodName, cals, proteins));

                    updateDailyViews();
                }
        );

        updateDailyViews();
    }

    private void updateDailyViews() {
        TextView dailyCalSum = findViewById(R.id.tvDailyCals);
        TextView dailyProteinSum = findViewById(R.id.tvDailyProteins);
        TextView avgView = findViewById(R.id.tvDailyAverage);

        dailyCalSum.setText(calsSum.toString());
        dailyProteinSum.setText(proteinSum.toString());
        avgView.setText(String.format("%.2f",calcAverage(calsSum,proteinSum)));
    }

    private Double calcAverage(Integer calsSum, Integer proteinSum) {
        if (proteinSum == 0) return -1.0;
        return (double)calsSum/proteinSum;
    }

}
