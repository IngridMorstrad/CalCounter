package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
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

/**
 * A placeholder fragment containing a simple view.
 */
public class MainActivityFragment extends Fragment {

    public final static String PROTEINS = "com.ashwinmenon.www.CalCounter.PROTEINS";
    public final static String CALS = "com.ashwinmenon.www.CalCounter.CALS";
    public final static String FOODS = "com.ashwinmenon.www.CalCounter.FOODS";
    public final static String POSITION = "com.ashwinmenon.www.CalCounter.POS";
    Integer proteinsTotal, calsTotal;
    private ArrayList<String> days;
    public static ArrayList< ArrayList <Integer> > proteins;
    public static ArrayList< ArrayList <Integer> > cals;
    public static ArrayList< ArrayList <String> > foods;
    private ArrayAdapter<String> daysAdapter;
    private ListView lvItems;
    public final static String DAY_CLICKED = "com.ashwinmenon.www.CalCounter.DAY";
    private boolean displayWeek;

    public MainActivityFragment() {
    }

    private void readItems() {
        File filesDir = getActivity().getFilesDir();
        File calsFile = new File(filesDir, "cals.txt");
        LineIterator iter;
        cals = new ArrayList<ArrayList<Integer>>();
        try {
            iter = FileUtils.lineIterator(calsFile);
            while (iter.hasNext()) {
                String fileData = iter.next().toString();
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    cals.add(new ArrayList<Integer>());
                }
                else {
                    cals.get(cals.size() - 1).add(Integer.parseInt(fileData));
                }
            }
        } catch (IOException e) {
            cals = new ArrayList<ArrayList<Integer>>();
        } catch (ArrayIndexOutOfBoundsException e) {
            cals = new ArrayList<ArrayList<Integer>>();
        }
        File foodsFile = new File(filesDir, "foods.txt");
        foods = new ArrayList<ArrayList<String>>();
        try {
            iter = FileUtils.lineIterator(foodsFile);
            while (iter.hasNext()) {
                String fileData = iter.next().toString();
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    foods.add(new ArrayList<String>());
                }
                else {
                    foods.get(foods.size() - 1).add(fileData);
                }
            }
        } catch (IOException e) {
            foods = new ArrayList<ArrayList<String>>();
        } catch (ArrayIndexOutOfBoundsException e) {
            foods = new ArrayList<ArrayList<String>>();
        }
        File proteinsFile = new File(filesDir, "proteins.txt");
        proteins = new ArrayList<ArrayList<Integer>>();
        try {
            iter = FileUtils.lineIterator(proteinsFile);
            while (iter.hasNext()) {
                String fileData = iter.next().toString();
                if (fileData.length() >= 6 && fileData.substring(0,6).equals("<DATE>")) {
                    proteins.add(new ArrayList<Integer>());
                }
                else {
                    proteins.get(proteins.size() - 1).add(Integer.parseInt(fileData));
                }
            }
        } catch (IOException e) {
            proteins = new ArrayList<ArrayList<Integer>>();
        } catch (ArrayIndexOutOfBoundsException e) {
            proteins = new ArrayList<ArrayList<Integer>>();
        }

    }

    private void writeItems() {
        File filesDir = getActivity().getFilesDir();
        File calsFile = new File(filesDir, "cals.txt");
        try {
            FileUtils.writeStringToFile(calsFile, "");
            for (ArrayList<Integer> dayCals: cals) {
                FileUtils.writeStringToFile(calsFile,"<DATE>\n",true);
                FileUtils.writeLines(calsFile,dayCals,true);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        File proteinsFile = new File(filesDir, "proteins.txt");
        try {
            FileUtils.writeStringToFile(proteinsFile, "");
            for (ArrayList<Integer> dayCals: proteins) {
                FileUtils.writeStringToFile(proteinsFile,"<DATE>\n",true);
                FileUtils.writeLines(proteinsFile,dayCals,true);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        File foodsFile = new File(filesDir, "foods.txt");
        try {
            FileUtils.writeStringToFile(foodsFile,"");
            for (ArrayList<String> dayCals: foods) {
                FileUtils.writeStringToFile(foodsFile,"<DATE>\n",true);
                FileUtils.writeLines(foodsFile,dayCals,true);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        SimpleDateFormat curFormatter = new SimpleDateFormat("dd/MM/yyyy");
        Date startDay, currDay;
        startDay = new Date();
        currDay = new Date();
        days = new ArrayList<String>();
        Calendar c = Calendar.getInstance();

        try {
            startDay = curFormatter.parse("30/05/2016");
        } catch (ParseException e) {
            e.printStackTrace();
        }
        try {
            currDay = curFormatter.parse(curFormatter.format(c.getTime()));
        } catch (ParseException e) {
            e.printStackTrace();
        }
        GregorianCalendar gCal = new GregorianCalendar();
        gCal.setTime(startDay);
        Integer dayscnt = 0;
        for (; !gCal.getTime().after(currDay); gCal.add(Calendar.DATE, 1)) {
            days.add(curFormatter.format(gCal.getTime()));
            dayscnt++;
        }

        readItems();
        while (proteins.size() < dayscnt) proteins.add(new ArrayList<Integer>());
        while (foods.size() < dayscnt) foods.add(new ArrayList<String>());
        while (cals.size() < dayscnt) cals.add(new ArrayList<Integer>());
        daysAdapter = new ArrayAdapter<String>(this.getActivity(),
                android.R.layout.simple_list_item_1, days);

        proteinsTotal = 0;
        calsTotal = 0;
        displayWeek = false;
        super.onCreate(savedInstanceState);
    }

    // Attaches a long click listener to the listview
    private void setupListViewListener() {
        lvItems.setOnItemClickListener(
                new AdapterView.OnItemClickListener() {

                    @Override
                    public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                        Intent intent = new Intent(getActivity(), FoodActivity.class);
                        intent.putExtra(DAY_CLICKED, days.get(position));
                        intent.putExtra(POSITION, position);
                        intent.putIntegerArrayListExtra(PROTEINS, proteins.get(position));
                        intent.putIntegerArrayListExtra(CALS, cals.get(position));
                        intent.putStringArrayListExtra(FOODS, foods.get(position));
                        startActivity(intent);
                        // Refresh the adapter
                        //daysAdapter.notifyDataSetChanged();
                        //writeItems();
                    }

                });
    }

    private void updateDisplay() {
        Activity a = getActivity();
        TextView proteinsView = (TextView) a.findViewById(R.id.proteins);
        TextView calsView = (TextView) a.findViewById(R.id.calories);
        TextView avgView = (TextView) a.findViewById(R.id.avg);
        Integer proteinSum = 0, calSum = 0;

        Double average = 0.0;

        int day = 0;
        if (displayWeek) day = Math.max(day, proteins.size() - 7);
        for(; day < proteins.size(); day++) {
            for (Integer i: proteins.get(day)) {
                proteinSum += i;
            }
            for (Integer i: cals.get(day)) {
                calSum += i;
            }
        }

        proteinsView.setText(proteinSum.toString());
        calsView.setText(calSum.toString());
        if (proteinSum != 0) {
            average = (double)calSum/proteinSum;
        }

        avgView.setText(String.format("%.2f",average));
    }

    @Override
    public void onResume() {
        super.onResume();

        updateDisplay();
        writeItems();
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.fragment_main, container, false);

        lvItems = (ListView) rootView.findViewById(R.id.lvItems);

        lvItems.setAdapter(daysAdapter);

        View cals = rootView.findViewById(R.id.calories);
        cals.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                displayWeek = !displayWeek;
                updateDisplay();
            }
        });

        setupListViewListener();

        return rootView;
    }
}
