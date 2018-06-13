package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import android.app.Fragment;
import android.content.Intent;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.TextView;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.LineIterator;

import java.io.File;
import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.List;

/**
 * A placeholder fragment containing a simple view.
 */
public class MainActivityFragment extends Fragment {

    // TODO: Refactor to use food file or a database
    // TODO: USDA Food API
    // TODO: Ability to add multiple of same food
    // TODO: Add sort by cals/proteins/ratio & asc/desc
    // TODO: Add option to colour foods by ratio/calorie/protein
    final static String POSITION = "com.ashwinmenon.www.CalCounter.POS";
    static int daysToQuery;
    static boolean displayFilter;
    private List<String> days;
    static List< ArrayList <Food> > foods;
    private ArrayAdapter<String> daysAdapter;
    private ListView lvItems;

    private void readNewItems() {
        File filesDir = getActivity().getFilesDir();
        File foodsFile = new File(filesDir, "foodsNew.txt");
        LineIterator iter;
        foods = new ArrayList<>();
        try {
            iter = FileUtils.lineIterator(foodsFile);
            while (iter.hasNext()) {
                String fileData = iter.next();
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    foods.add(new ArrayList<>());
                }
                else {
                    String[] foodDetails = fileData.split("[<]+");
                    foods.get(foods.size() - 1).add(new Food(foodDetails[0], Integer.parseInt(foodDetails[1]), Integer.parseInt(foodDetails[2])));
                }
            }
        } catch (ArrayIndexOutOfBoundsException | IOException e) {
            foods = new ArrayList<>();
        }
    }

    private void readItems() {
        File filesDir = getActivity().getFilesDir();
        File foodsFile = new File(filesDir, "foods.txt");
        LineIterator iter;
        foods = new ArrayList<>();
        try {
            iter = FileUtils.lineIterator(foodsFile);
            while (iter.hasNext()) {
                String fileData = iter.next();

                System.out.println("FOODS: " + fileData);
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    foods.add(new ArrayList<>());
                }
                else {
                    foods.get(foods.size() - 1).add(new Food(fileData));
                }
            }
        } catch (ArrayIndexOutOfBoundsException | IOException e) {
            foods = new ArrayList<>();
        }
        File calsFile = new File(filesDir, "cals.txt");
        int currDatePos = -1, currFoodPos = 0;
        try {
            iter = FileUtils.lineIterator(calsFile);
            while (iter.hasNext()) {
                String fileData = iter.next();
                System.out.println("CALS: " + fileData);
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    currDatePos++;
                    currFoodPos = 0;
                }
                else {
                    foods.get(currDatePos).get(currFoodPos).setCalories(Integer.parseInt(fileData));
                    currFoodPos++;
                }
            }
        } catch (IOException | ArrayIndexOutOfBoundsException e) {
            // pass
        }
        File proteinsFile = new File(filesDir, "proteins.txt");
        currDatePos = -1;
        currFoodPos = 0;
        try {
            iter = FileUtils.lineIterator(proteinsFile);
            while (iter.hasNext()) {
                String fileData = iter.next();
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    currDatePos++;
                    currFoodPos = 0;
                }
                else {
                    foods.get(currDatePos).get(currFoodPos).setProteins(Integer.parseInt(fileData));
                    currFoodPos++;
                }
            }
        } catch (IOException | ArrayIndexOutOfBoundsException e) {
            // pass
        }

    }

    private void writeItems() {
        File filesDir = getActivity().getFilesDir();
        File foodsFile = new File(filesDir, "foodsNew.txt");
        try {
            FileUtils.writeStringToFile(foodsFile, "");
            for (ArrayList<Food> dayFoods: foods) {
                FileUtils.writeStringToFile(foodsFile,"<DATE>\n",true);
                FileUtils.writeLines(foodsFile,dayFoods,true);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        SimpleDateFormat curFormatter = new SimpleDateFormat("dd/MM/yyyy");
        Date startDay, currDay;
        GregorianCalendar gCal;

        startDay = new Date();
        currDay = new Date();
        days = new ArrayList<>();

        try {
            String startDate = "30/05/2018";
            startDay = curFormatter.parse(startDate);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        try {
            currDay = curFormatter.parse(curFormatter.format(Calendar.getInstance().getTime()));
        } catch (ParseException e) {
            e.printStackTrace();
        }

        gCal = new GregorianCalendar();
        gCal.setTime(startDay);
        for (; !gCal.getTime().after(currDay); gCal.add(Calendar.DATE, 1)) {
            days.add(0,curFormatter.format(gCal.getTime()));
        }

        readNewItems();

        while (foods.size() < days.size()) foods.add(new ArrayList<>());

        displayFilter = false;

        daysAdapter = new DayAdapter(getActivity(), days);

        super.onCreate(savedInstanceState);
    }

    // Add an ItemClickListener to start an activity where we can add foods for the day clicked
    private void setupListViewListener() {
        lvItems.setOnItemClickListener(
                (parent, view, position, id) -> {
                    Intent intent = new Intent(getActivity(), FoodActivity.class);
                    intent.putExtra(POSITION, days.size() - 1 - position);
                    startActivity(intent);
                });
    }

    private View getViewByPosition(int pos, ListView listView) {
        final int firstListItemPosition = listView.getFirstVisiblePosition();
        final int lastListItemPosition = firstListItemPosition + listView.getChildCount() - 1;

        if (pos < firstListItemPosition || pos > lastListItemPosition ) {
            return listView.getAdapter().getView(pos, null, listView);
        } else {
            final int childIndex = pos - firstListItemPosition;
            return listView.getChildAt(childIndex);
        }
    }

    private void updateDisplay() {
        Activity a = getActivity();
        TextView proteinsView = a.findViewById(R.id.proteins);
        TextView calsView = a.findViewById(R.id.calories);
        TextView ratioView = a.findViewById(R.id.avg);
        int proteinSum = 0, calSum = 0;
        double ratio = 0.0;

        int day = Math.max(0, foods.size() - daysToQuery);

        for(; day < foods.size(); day++) {
            for (Food f : foods.get(day)) {
                proteinSum += f.getProteinsInt();
                calSum += f.getCaloriesInt();
            }
        }

        if (displayFilter) {
            proteinsView.setText(String.format("%.2f",(double) proteinSum/daysToQuery));
            calsView.setText(String.format("%.2f",(double) calSum/daysToQuery));
        }
        else {
            proteinsView.setText(String.valueOf(proteinSum));
            calsView.setText(String.valueOf(calSum));
        }

        if (proteinSum != 0) {
            ratio = (double) calSum/proteinSum;
        }

        ratioView.setText(String.format("%.2f",ratio));
        daysAdapter.notifyDataSetChanged();
    }

    @Override
    public void onResume() {
        super.onResume();

        daysToQuery = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(getActivity()).getString(getActivity().getString(R.string.key_days),"7"));
        updateDisplay();
        writeItems();
    }

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.fragment_main, container, false);

        lvItems = rootView.findViewById(R.id.lvItems);

        lvItems.setAdapter(daysAdapter);

        View cals = rootView.findViewById(R.id.calories);

        cals.setOnClickListener(v -> {
            displayFilter = !displayFilter;
            updateDisplay();
        });

        setupListViewListener();

        return rootView;
    }
}
