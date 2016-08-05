package com.ashwinmenon.www.calcounter;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;

public class FoodActivity extends AppCompatActivity {

    ArrayAdapter <String> dailyFoodAdapter;
    ArrayAdapter <Integer> dailyCalsAdapter;
    ArrayAdapter <Integer> dailyProteinsAdapter;
    private Integer proteinSum, calsSum, pos;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_food);
        Intent intent = getIntent();

        pos = intent.getIntExtra(MainActivityFragment.POSITION, -1);
        if (pos == -1) {
            Toast T = Toast.makeText(this, "POSITION ERROR", Toast.LENGTH_LONG);
            T.show();
            return;
        }

        proteinSum = sumArrayList(MainActivityFragment.proteins.get(pos));
        calsSum = sumArrayList(MainActivityFragment.cals.get(pos));

        dailyFoodAdapter = new ArrayAdapter<String>(this, android.R.layout.simple_list_item_1, MainActivityFragment.foods.get(pos));
        dailyCalsAdapter = new ArrayAdapter<Integer>(this, android.R.layout.simple_list_item_1, MainActivityFragment.cals.get(pos));
        dailyProteinsAdapter = new ArrayAdapter<Integer>(this, android.R.layout.simple_list_item_1, MainActivityFragment.proteins.get(pos));

        Button addFood = (Button) findViewById(R.id.btnAdd);

        AdapterView.OnItemClickListener showRatio = new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                int calories = MainActivityFragment.cals.get(pos).get(position);
                int proteins = MainActivityFragment.proteins.get(pos).get(position);
                String message = "";
                if (proteins == 0) {
                    message = "Get some more protein!";
                }
                else {
                    message = String.format("%.2f", (double)calories/proteins);
                }
                Toast ratio = Toast.makeText(getApplicationContext(), message, Toast.LENGTH_SHORT);
                ratio.show();
            }
        };

        AdapterView.OnItemLongClickListener deleteItem = new AdapterView.OnItemLongClickListener() {
            @Override
            public boolean onItemLongClick(AdapterView<?> parent, View view, int position, long id) {
                //String item = MainActivityFragment.foods.get(pos).get(position);
                MainActivityFragment.foods.get(pos).remove(position);
                calsSum -= MainActivityFragment.cals.get(pos).get(position);
                MainActivityFragment.cals.get(pos).remove(position);
                proteinSum -= MainActivityFragment.proteins.get(pos).get(position);
                MainActivityFragment.proteins.get(pos).remove(position);

                updateDailyViews();
                // Refresh the adapter
                dailyFoodAdapter.notifyDataSetChanged();
                dailyCalsAdapter.notifyDataSetChanged();
                dailyProteinsAdapter.notifyDataSetChanged();

                // Return true consumes the long click event (marks it handled)
                return true;
            }
        };

        ListView lvFoods = (ListView) findViewById(R.id.lvFoods);
        lvFoods.setAdapter(dailyFoodAdapter);

        ListView lvCals = (ListView) findViewById(R.id.lvCals);
        lvCals.setAdapter(dailyCalsAdapter);

        ListView lvProteins = (ListView) findViewById(R.id.lvProteins);
        lvProteins.setAdapter(dailyProteinsAdapter);

        lvFoods.setOnItemClickListener(showRatio);
        lvCals.setOnItemClickListener(showRatio);
        lvProteins.setOnItemClickListener(showRatio);

        lvFoods.setOnItemLongClickListener(deleteItem);
        lvCals.setOnItemLongClickListener(deleteItem);
        lvProteins.setOnItemLongClickListener(deleteItem);

        addFood.setOnClickListener(
            new View.OnClickListener() {
                @Override
                public void onClick(View v) {
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

                    dailyFoodAdapter.add(foodName);
                    dailyProteinsAdapter.add(proteins);
                    dailyCalsAdapter.add(cals);

                    updateDailyViews();
                }
            }
        );

        updateDailyViews();
    }

    private void updateDailyViews() {
        TextView dailyCalSum = (TextView) findViewById(R.id.tvDailyCals);
        TextView dailyProteinSum = (TextView) findViewById(R.id.tvDailyProteins);
        TextView avgView = (TextView) findViewById(R.id.tvDailyAverage);

        dailyCalSum.setText(calsSum.toString());
        dailyProteinSum.setText(proteinSum.toString());
        avgView.setText(String.format("%.2f",calcAverage(calsSum,proteinSum)));
    }

    private Double calcAverage(Integer calsSum, Integer proteinSum) {
        if (proteinSum == 0) return -1.0;
        return (double)calsSum/proteinSum;
    }

    private Integer sumArrayList(ArrayList<Integer> integers) {
        Integer ans = 0;
        for (int i: integers) ans += i;
        return ans;
    }

}
