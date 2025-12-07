import 'package:flutter/material.dart';

void main() {
  runApp(const CalendarApp());
}

class CalendarApp extends StatelessWidget {
  const CalendarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Calendar',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF4F5F7),
        textTheme: Theme.of(context).textTheme.apply(fontFamily: 'Roboto'),
      ),
      home: const CalendarHomePage(),
    );
  }
}

class CalendarHomePage extends StatefulWidget {
  const CalendarHomePage({super.key});

  @override
  State<CalendarHomePage> createState() => _CalendarHomePageState();
}

class _CalendarHomePageState extends State<CalendarHomePage> {
  static const List<String> _monthNames = [
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
  ];

  static const List<String> _weekdayLabels = [
    'ПН',
    'ВТ',
    'СР',
    'ЧТ',
    'ПТ',
    'СБ',
    'ВС',
  ];

  final DateTime _today = DateTime.now();
  late DateTime _visibleMonth;
  DateTime? _pickedDay;

  @override
  void initState() {
    super.initState();
    _visibleMonth = DateTime(_today.year, _today.month);
    _pickedDay = _today;
  }

  bool get _showsCurrentMonth =>
      _visibleMonth.year == _today.year && _visibleMonth.month == _today.month;

  void _shiftMonth(int delta) {
    setState(() {
      _visibleMonth = DateTime(_visibleMonth.year, _visibleMonth.month + delta);
    });
  }

  void _shiftYear(int delta) {
    setState(() {
      _visibleMonth = DateTime(_visibleMonth.year + delta, _visibleMonth.month);
    });
  }

  void _jumpToToday() {
    setState(() {
      _visibleMonth = DateTime(_today.year, _today.month);
      _pickedDay = _today;
    });
  }

  void _handleDayTap(DateTime day) {
    setState(() {
      _pickedDay = day;
      // Если пользователь ткнул по дню из соседнего месяца — смещаем сетку.
      _visibleMonth = DateTime(day.year, day.month);
    });
  }

  List<DateTime> _generateMonthCells() {
    final firstDayOfMonth = DateTime(_visibleMonth.year, _visibleMonth.month, 1);
    final mondayBasedIndex = (firstDayOfMonth.weekday + 6) % 7;
    final gridStart = firstDayOfMonth.subtract(Duration(days: mondayBasedIndex));

    // Всегда рисуем шесть недель (6 * 7 = 42 ячейки), чтобы макет был устойчивым.
    return List.generate(
      42,
      (index) => DateTime(
        gridStart.year,
        gridStart.month,
        gridStart.day + index,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final calendarCells = _generateMonthCells();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Calendar'),
        centerTitle: true,
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x15000000),
                    blurRadius: 18,
                    offset: Offset(0, 8),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
                child: Column(
                  children: [
                    _MonthHeader(
                      monthLabel:
                          '${_monthNames[_visibleMonth.month - 1]} ${_visibleMonth.year}',
                      onPrevPressed: () => _shiftMonth(-1),
                      onNextPressed: () => _shiftMonth(1),
                    ),
                    const SizedBox(height: 12),
                    _YearSelector(
                      year: _visibleMonth.year,
                      onAddYear: () => _shiftYear(1),
                      onRemoveYear: () => _shiftYear(-1),
                    ),
                    if (!_showsCurrentMonth) ...[
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton.icon(
                          onPressed: _jumpToToday,
                          icon: const Icon(Icons.calendar_today_outlined, size: 18),
                          label: const Text('Вернуться к текущему месяцу'),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _WeekdayRow(labels: _weekdayLabels),
            const SizedBox(height: 8),
            Expanded(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x14000000),
                      blurRadius: 14,
                      offset: Offset(0, 6),
                    ),
                  ],
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: GridView.builder(
                    itemCount: calendarCells.length,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 7,
                      mainAxisSpacing: 6,
                      crossAxisSpacing: 6,
                    ),
                    itemBuilder: (context, index) {
                      final day = calendarCells[index];
                      final isToday =
                          day.year == _today.year &&
                              day.month == _today.month &&
                              day.day == _today.day;
                      final isSelected = _pickedDay != null &&
                          day.year == _pickedDay!.year &&
                          day.month == _pickedDay!.month &&
                          day.day == _pickedDay!.day;
                      final isOutOfMonth = day.month != _visibleMonth.month;

                      return _DayCell(
                        day: day,
                        isToday: isToday,
                        isSelected: isSelected,
                        isOutOfMonth: isOutOfMonth,
                        onTap: () => _handleDayTap(day),
                        textTheme: textTheme,
                      );
                    },
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (_pickedDay != null)
              _PickedDayLabel(date: _pickedDay!),
          ],
        ),
      ),
    );
  }
}

class _MonthHeader extends StatelessWidget {
  const _MonthHeader({
    required this.monthLabel,
    required this.onPrevPressed,
    required this.onNextPressed,
  });

  final String monthLabel;
  final VoidCallback onPrevPressed;
  final VoidCallback onNextPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: onPrevPressed,
          icon: const Icon(Icons.chevron_left),
          tooltip: 'Предыдущий месяц',
        ),
        Expanded(
          child: Text(
            monthLabel,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
        IconButton(
          onPressed: onNextPressed,
          icon: const Icon(Icons.chevron_right),
          tooltip: 'Следующий месяц',
        ),
      ],
    );
  }
}

class _YearSelector extends StatelessWidget {
  const _YearSelector({
    required this.year,
    required this.onAddYear,
    required this.onRemoveYear,
  });

  final int year;
  final VoidCallback onAddYear;
  final VoidCallback onRemoveYear;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          onPressed: onRemoveYear,
          icon: const Icon(Icons.remove_circle_outline),
          tooltip: 'Год назад',
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(30),
            color: const Color(0xFFE6F4F1),
          ),
          child: Text(
            '$year',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        IconButton(
          onPressed: onAddYear,
          icon: const Icon(Icons.add_circle_outline),
          tooltip: 'Год вперед',
        ),
      ],
    );
  }
}

class _WeekdayRow extends StatelessWidget {
  const _WeekdayRow({required this.labels});

  final List<String> labels;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: labels
          .map(
            (name) => Expanded(
              child: Center(
                child: Text(
                  name,
                  style: Theme.of(context)
                      .textTheme
                      .labelLarge
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
              ),
            ),
          )
          .toList(),
    );
  }
}

class _DayCell extends StatelessWidget {
  const _DayCell({
    required this.day,
    required this.isToday,
    required this.isSelected,
    required this.isOutOfMonth,
    required this.onTap,
    required this.textTheme,
  });

  final DateTime day;
  final bool isToday;
  final bool isSelected;
  final bool isOutOfMonth;
  final VoidCallback onTap;
  final TextTheme textTheme;

  @override
  Widget build(BuildContext context) {
    final Color baseColor =
        isSelected ? Theme.of(context).colorScheme.primary : Colors.white;
    final Color outlineColor = isToday
        ? Theme.of(context).colorScheme.primary
        : Colors.grey.shade300;
    final Color textColor = isSelected
        ? Colors.white
        : (isOutOfMonth ? Colors.grey.shade500 : Colors.black87);

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: baseColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? Colors.transparent : outlineColor,
            width: isToday ? 2 : 1,
          ),
        ),
        child: Center(
          child: Text(
            '${day.day}',
            style: textTheme.bodyLarge?.copyWith(
              color: textColor,
              fontWeight: isToday ? FontWeight.w700 : FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }
}

class _PickedDayLabel extends StatelessWidget {
  const _PickedDayLabel({required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final formatted =
        '${date.day.toString().padLeft(2, '0')}.${date.month.toString().padLeft(2, '0')}.${date.year}';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: Colors.white,
        boxShadow: const [
          BoxShadow(
            color: Color(0x12000000),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Text(
        'Вы выбрали: $formatted',
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyLarge,
      ),
    );
  }
}
