package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"math/rand"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/xuri/excelize/v2"
)

const (
	adminRootID    = 7973895358 // Главный админ
	dataFile       = "attendance.csv"
	usersFile      = "users.csv"
	adminsFile     = "admins.csv"
	dateFormat     = "02.01.2006 15:04:05"
	reportHour     = 19
	reminderHour   = 18
	reminderMinute = 30
	exportLimit    = 10000 // максимум строк на экспорт
)

var (
	botToken             string
	pendingNameInput     = make(map[int]bool)
	pendingLocationInput = make(map[int]bool)
	tempLocation         = make(map[int]string)
	randText             = rand.New(rand.NewSource(time.Now().UnixNano()))
	leaveLocations       = []string{
		"🏥 Поликлиника", "⚓️ ОБРМП", "🌆 Калининград", "🛒 Магазин", "🍲 Столовая",
		"🏨 Госпиталь", "⚙️ Хоз. Работы", "🩺 ВВК", "🏛 МФЦ", "🚓 Патруль", "📝 Другое",
	}
	reminderTexts = []string{
		"🦉 Не забудь вернуться в часть! Солдат всегда возвращается домой.",
		"🌚 Уже вечер — пора бы прибыть!",
		"🚨 Командир волнуется — отметь прибытие!",
		"🐻 Пора домой, жду тебя!",
		"😜 Твои друзья уже здесь, а ты?",
		"🎯 Не пропусти отметку 'Прибыл', а то придется угощать всех чаем!",
		"🥟 Ужин стынет — прибудь, пока горячо!",
		"📢 Объявление: пора отмечать прибытие!",
	}
	adminRights = []struct {
		Code string
		Name string
	}{
		{"summary", "📊 Сводка"},
		{"export", "📥 Экспорт"},
		{"manage_users", "👥 Управление ЛС"},
		{"settings", "⚙️ Настройки"},
		{"danger_zone", "⚠️ Опасная зона"},
	}
	emojiRegex = regexp.MustCompile(`[\p{So}\p{Cn}\p{Sk}\p{Co}\p{Cs}\x{1F600}-\x{1F64F}\x{1F300}-\x{1F5FF}\x{1F680}-\x{1F6FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}\x{1F900}-\x{1F9FF}\x{1F1E6}-\x{1F1FF}]+`)
)

type User struct {
	ID     int
	Name   string
	ChatID int64
}

type Admin struct {
	ID    int
	Name  string
	Rights map[string]bool
}

func main() {
	botToken = os.Getenv("TELEGRAM_TOKEN")
	if botToken == "" {
		fmt.Println("Ошибка: TELEGRAM_TOKEN не найден (задать в Render Settings > Environment)!")
		return
	}
	StartKeepAlive()

	bot, err := tgbotapi.NewBotAPI(botToken)
	if err != nil {
		log.Panic(err)
	}
	bot.Debug = false
	fmt.Println("Бот Tabel-Go-Bot запущен!")

	go reminderScheduler(bot)
	go dailyReportScheduler(bot)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60
	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message != nil {
			if update.Message.IsCommand() {
				handleCommand(bot, update.Message)
				go func(chatID int64, msgID int) {
					time.Sleep(60 * time.Second)
					bot.Request(tgbotapi.DeleteMessageConfig{
						ChatID:    chatID,
						MessageID: msgID,
					})
				}(update.Message.Chat.ID, update.Message.MessageID)
				continue
			}
			handleMessage(bot, update.Message)
		}
		if update.CallbackQuery != nil {
			handleAction(bot, update.CallbackQuery)
		}
	}
}
func handleCommand(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	userID := msg.From.ID
	if msg.Command() == "start" {
		if !isUserRegistered(userID) {
			pendingNameInput[userID] = true
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✍️ Введите своё ФИО в формате: Фамилия И.О. (например: Иванов И.И.)"))
			return
		}
		sendMainMenu(bot, msg.Chat.ID, msg.From)
		return
	}

	if !isUserRegistered(userID) {
		pendingNameInput[userID] = true
		bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✍️ Введите своё ФИО в формате: Фамилия И.О. (например: Иванов И.И.)"))
		return
	}

	switch msg.Command() {
	case "setname":
		args := msg.CommandArguments()
		if args == "" || !isValidName(args) {
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✏️ Введите: /setname Фамилия И.О. (например: Иванов И.И.)"))
			return
		}
		saveUserName(userID, args, msg.Chat.ID)
		bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✅ ФИО обновлено!"))
		sendMainMenu(bot, msg.Chat.ID, msg.From)
	case "admin":
		if isRootAdmin(userID) || isAdminWithRight(userID, "settings") {
			sendAdminPanel(bot, msg.Chat.ID)
		}
	case "report":
		if isRootAdmin(userID) || isAdminWithRight(userID, "export") {
			msg := tgbotapi.NewMessage(msg.Chat.ID, "Выберите период для экспорта:")
			msg.ReplyMarkup = reportFilterMenu()
			bot.Send(msg)
		}
	case "clear":
		if isRootAdmin(userID) || isAdminWithRight(userID, "danger_zone") {
			os.Remove(dataFile)
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "🗑️ Журнал посещений очищен"))
		}
	case "list":
		if isRootAdmin(userID) || isAdminWithRight(userID, "manage_users") {
			list := getUserList()
			if list == "" {
				list = "Нет данных о сотрудниках."
			}
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "👥 Список сотрудников:\n"+list))
		}
	}
}

func handleMessage(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	userID := msg.From.ID

	if pendingNameInput[userID] {
		name := strings.TrimSpace(msg.Text)
		if isValidName(name) {
			saveUserName(userID, name, msg.Chat.ID)
			delete(pendingNameInput, userID)
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✅ ФИО сохранено!"))
			sendMainMenu(bot, msg.Chat.ID, msg.From)
		} else {
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "❗ Формат неверный. Введите ФИО так: Иванов И.И."))
		}
		return
	}
	if pendingLocationInput[userID] {
		manualLocation := strings.TrimSpace(msg.Text)
		if manualLocation == "" || len([]rune(manualLocation)) < 3 {
			bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "❗ Введите корректную локацию (не менее 3 символов)."))
			return
		}
		now := time.Now().Format(dateFormat)
		name := getUserName(userID, msg.From)
		saveAttendance(now, strconv.Itoa(userID), name, "Убыл", manualLocation)
		notifyAdminAboutMark(bot, userID, name, "Убыл", manualLocation, now)
		delete(pendingLocationInput, userID)
		bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "✅ Убытие отмечено!"))
		sendMainMenu(bot, msg.Chat.ID, msg.From)
		return
	}
}

func sendMainMenu(bot *tgbotapi.BotAPI, chatID int64, user *tgbotapi.User) {
	userID := user.ID
	isAdmin := isRootAdmin(userID) || isAdminAny(userID)
	row := []tgbotapi.InlineKeyboardButton{
		tgbotapi.NewInlineKeyboardButtonData("🟢 Прибыл", "arrived"),
		tgbotapi.NewInlineKeyboardButtonData("🔴 Убыл", "left"),
		tgbotapi.NewInlineKeyboardButtonData("📖 Журнал", "journal"),
	}
	if isAdmin {
		row = append(row, tgbotapi.NewInlineKeyboardButtonData("⚙️ Админ-панель", "admin_panel"))
	}
	msg := tgbotapi.NewMessage(chatID, "Главное меню")
	msg.ReplyMarkup = tgbotapi.NewInlineKeyboardMarkup(row)
	bot.Send(msg)
}

func handleAction(bot *tgbotapi.BotAPI, query *tgbotapi.CallbackQuery) {
	user := query.From
	userID := user.ID
	chatID := query.Message.Chat.ID
	name := getUserName(userID, user)
	now := time.Now().Format(dateFormat)

	switch query.Data {
	case "arrived":
		lastAction, _ := getLastAction(userID)
		if lastAction == "Прибыл" {
			bot.Send(tgbotapi.NewMessage(chatID, "⚠️ Ты ещё не отмечал убытие — всё ок?"))
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Сначала отметь убытие"))
			return
		}
		saveAttendance(now, strconv.Itoa(userID), name, "Прибыл", "-")
		notifyAdminAboutMark(bot, userID, name, "Прибыл", "-", now)
		bot.Send(tgbotapi.NewMessage(chatID, "✅ Прибытие отмечено!"))
		sendMainMenu(bot, chatID, user)
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Записано!"))
	case "left":
		lastAction, _ := getLastAction(userID)
		if lastAction == "Убыл" {
			bot.Send(tgbotapi.NewMessage(chatID, "🔴 Ты уже отмечал убытие. Сначала отметь прибытие!"))
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Сначала отметь прибытие"))
			return
		}
		msg := tgbotapi.NewMessage(chatID, "Выберите локацию, куда убыл:")
		msg.ReplyMarkup = leaveMenu()
		bot.Send(msg)
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Выберите локацию"))
	case "journal":
		entries := getLastActions(strconv.Itoa(userID), 3)
		if len(entries) == 0 {
			msg := tgbotapi.NewMessage(chatID, "Записей не найдено.")
			bot.Send(msg)
		} else {
			var resp strings.Builder
			for _, e := range entries {
				date, timePart := splitDateTime(e[0])
				actEmoji := "❓"
				if e[3] == "Прибыл" {
					actEmoji = "🟢"
				} else if e[3] == "Убыл" {
					actEmoji = "🔴"
				}
				loc := e[4]
				resp.WriteString(fmt.Sprintf("%s %s %s\n%s | %s | %s\n\n", actEmoji, e[3], loc, date, timePart, e[2]))
			}
			msg := tgbotapi.NewMessage(chatID, resp.String())
			bot.Send(msg)
		}
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Журнал"))
	case "admin_panel":
		if isRootAdmin(userID) || isAdminAny(userID) {
			sendAdminPanel(bot, chatID)
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Открыта админ-панель"))
		}
	case "personnel":
		sendPersonnelList(bot, chatID, 0)
	case "add_admin":
		sendPersonnelForAdmin(bot, chatID, 0)
	case "manage_admins":
		sendAdminsList(bot, chatID, 0)
	case "summary":
		adminSummary(bot, chatID)
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Быстрая сводка"))
	case "export_today":
		sendFilteredExcel(bot, chatID, filterToday)
	case "export_yesterday":
		sendFilteredExcel(bot, chatID, filterYesterday)
	case "export_7days":
		sendFilteredExcel(bot, chatID, filterLastNDays(7))
	case "export_30days":
		sendFilteredExcel(bot, chatID, filterLastNDays(30))
	default:
		// Обработка для листалок и прав
		if strings.HasPrefix(query.Data, "personnel_") {
			idx, _ := strconv.Atoi(strings.TrimPrefix(query.Data, "personnel_"))
			sendPersonnelList(bot, chatID, idx)
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, ""))
			return
		}
		if strings.HasPrefix(query.Data, "adminlist_") {
			idx, _ := strconv.Atoi(strings.TrimPrefix(query.Data, "adminlist_"))
			sendAdminsList(bot, chatID, idx)
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, ""))
			return
		}
		if strings.HasPrefix(query.Data, "makeadmin_") {
			idx, _ := strconv.Atoi(strings.TrimPrefix(query.Data, "makeadmin_"))
			users := getSortedUsers()
			if idx >= 0 && idx < len(users) {
				sendRightsCheckboxMenu(bot, chatID, users[idx].ID, nil)
			}
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, ""))
			return
		}
		if strings.HasPrefix(query.Data, "right_") {
			parts := strings.Split(query.Data, "_")
			if len(parts) != 3 {
				return
			}
			code := parts[1]
			uid, _ := strconv.Atoi(parts[2])
			current := getAdminRights(uid)
			current[code] = !current[code]
			sendRightsCheckboxMenu(bot, chatID, uid, current)
			bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, ""))
			return
		}
		if strings.HasPrefix(query.Data, "save_rights_") {
			uid, _ := strconv.Atoi(strings.TrimPrefix(query.Data, "save_rights_"))
			current := getAdminRights(uid)
			userName := getUserName(uid, nil)
			saveAdminRights(uid, userName, current)
			bot.Send(tgbotapi.NewMessage(chatID, fmt.Sprintf("✅ Права сохранены для %s", userName)))
			return
		}
		// Для локаций
		for i, loc := range leaveLocations {
			if query.Data == loc {
				if loc == "📝 Другое" {
					pendingLocationInput[userID] = true
					bot.Send(tgbotapi.NewMessage(chatID, "Введите вручную, куда выбываете:"))
					bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Жду текст"))
				} else {
					now := time.Now().Format(dateFormat)
					name := getUserName(userID, user)
					saveAttendance(now, strconv.Itoa(userID), name, "Убыл", loc)
					notifyAdminAboutMark(bot, userID, name, "Убыл", loc, now)
					bot.Send(tgbotapi.NewMessage(chatID, "✅ Убытие отмечено!"))
					sendMainMenu(bot, chatID, user)
					bot.AnswerCallbackQuery(tgbotapi.NewCallback(query.ID, "Записано!"))
				}
				return
			}
		}
	}
}
// --- Админ-панель и листалки ---

func sendAdminPanel(bot *tgbotapi.BotAPI, chatID int64) {
	msg := tgbotapi.NewMessage(chatID, "⚙️ Админ-панель:")
	kb := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("📊 Быстрая сводка", "summary"),
			tgbotapi.NewInlineKeyboardButtonData("👥 Личный состав", "personnel"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("📖 Журнал", "report"),
			tgbotapi.NewInlineKeyboardButtonData("📥 Экспорт", "report"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("👑 Управление админами", "manage_admins"),
			tgbotapi.NewInlineKeyboardButtonData("⚠️ Опасная зона", "danger"),
		),
	)
	msg.ReplyMarkup = kb
	bot.Send(msg)
}

func sendPersonnelList(bot *tgbotapi.BotAPI, chatID int64, idx int) {
	users := getSortedUsers()
	if len(users) == 0 {
		bot.Send(tgbotapi.NewMessage(chatID, "Нет данных о личном составе."))
		return
	}
	if idx < 0 {
		idx = 0
	}
	if idx >= len(users) {
		idx = len(users) - 1
	}
	u := users[idx]
	text := fmt.Sprintf("👤 <b>%s</b>\n🆔 <a href=\"tg://user?id=%d\">%d</a>", capitalizeName(u.Name), u.ID, u.ID)
	btns := []tgbotapi.InlineKeyboardButton{}
	if idx > 0 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", fmt.Sprintf("personnel_%d", idx-1)))
	}
	if idx < len(users)-1 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("Вперёд ▶️", fmt.Sprintf("personnel_%d", idx+1)))
	}
	// Кнопка "Назначить админом" (только если не root)
	if u.ID != adminRootID {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("👑 Назначить админом", fmt.Sprintf("makeadmin_%d", idx)))
	}
	kb := tgbotapi.NewInlineKeyboardMarkup(btns)
	msg := tgbotapi.NewMessage(chatID, text)
	msg.ParseMode = "HTML"
	msg.ReplyMarkup = kb
	bot.Send(msg)
}

func sendAdminsList(bot *tgbotapi.BotAPI, chatID int64, idx int) {
	admins := getAdmins()
	if len(admins) == 0 {
		bot.Send(tgbotapi.NewMessage(chatID, "Нет других админов."))
		return
	}
	if idx < 0 {
		idx = 0
	}
	if idx >= len(admins) {
		idx = len(admins) - 1
	}
	a := admins[idx]
	text := fmt.Sprintf("👑 <b>%s</b>\n🆔 <a href=\"tg://user?id=%d\">%d</a>\nПрава:", a.Name, a.ID, a.ID)
	for _, r := range adminRights {
		check := "⬜️"
		if a.Rights[r.Code] {
			check = "✅"
		}
		text += fmt.Sprintf("\n%s %s", check, r.Name)
	}
	btns := []tgbotapi.InlineKeyboardButton{}
	if idx > 0 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", fmt.Sprintf("adminlist_%d", idx-1)))
	}
	if idx < len(admins)-1 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("Вперёд ▶️", fmt.Sprintf("adminlist_%d", idx+1)))
	}
	kb := tgbotapi.NewInlineKeyboardMarkup(btns)
	msg := tgbotapi.NewMessage(chatID, text)
	msg.ParseMode = "HTML"
	msg.ReplyMarkup = kb
	bot.Send(msg)
}

func sendPersonnelForAdmin(bot *tgbotapi.BotAPI, chatID int64, idx int) {
	users := getSortedUsers()
	if len(users) == 0 {
		bot.Send(tgbotapi.NewMessage(chatID, "Нет данных о личном составе."))
		return
	}
	if idx < 0 {
		idx = 0
	}
	if idx >= len(users) {
		idx = len(users) - 1
	}
	u := users[idx]
	text := fmt.Sprintf("👤 <b>%s</b>\n🆔 <a href=\"tg://user?id=%d\">%d</a>", capitalizeName(u.Name), u.ID, u.ID)
	btns := []tgbotapi.InlineKeyboardButton{}
	if idx > 0 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", fmt.Sprintf("personnel_%d", idx-1)))
	}
	if idx < len(users)-1 {
		btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("Вперёд ▶️", fmt.Sprintf("personnel_%d", idx+1)))
	}
	btns = append(btns, tgbotapi.NewInlineKeyboardButtonData("👑 Назначить админом", fmt.Sprintf("makeadmin_%d", idx)))
	kb := tgbotapi.NewInlineKeyboardMarkup(btns)
	msg := tgbotapi.NewMessage(chatID, text)
	msg.ParseMode = "HTML"
	msg.ReplyMarkup = kb
	bot.Send(msg)
}

// Чекбокс-меню для назначения прав
func sendRightsCheckboxMenu(bot *tgbotapi.BotAPI, chatID int64, userID int, selected map[string]bool) {
	if selected == nil {
		selected = getAdminRights(userID)
	}
	var rows [][]tgbotapi.InlineKeyboardButton
	for _, right := range adminRights {
		check := "⬜️"
		if selected[right.Code] {
			check = "✅"
		}
		rows = append(rows, tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData(fmt.Sprintf("%s %s", check, right.Name), fmt.Sprintf("right_%s_%d", right.Code, userID)),
		))
	}
	rows = append(rows, tgbotapi.NewInlineKeyboardRow(
		tgbotapi.NewInlineKeyboardButtonData("💾 Сохранить", fmt.Sprintf("save_rights_%d", userID)),
	))
	kb := tgbotapi.NewInlineKeyboardMarkup(rows...)
	msg := tgbotapi.NewMessage(chatID, "Выберите права для админа:")
	msg.ReplyMarkup = kb
	bot.Send(msg)
}

// --- Админ-фильтры, экспорт Excel ---

func reportFilterMenu() tgbotapi.InlineKeyboardMarkup {
	return tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("📅 Сегодня", "export_today"),
			tgbotapi.NewInlineKeyboardButtonData("📆 Вчера", "export_yesterday"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("🗓️ 7 дней", "export_7days"),
			tgbotapi.NewInlineKeyboardButtonData("🗓️ 30 дней", "export_30days"),
		),
	)
}

func sendFilteredExcel(bot *tgbotapi.BotAPI, chatID int64, filter func([]string) bool) {
	rows := readCSV(dataFile)
	var filtered [][]string
	for _, row := range rows {
		if filter(row) {
			filtered = append(filtered, row)
		}
	}
	if len(filtered) == 0 {
		bot.Send(tgbotapi.NewMessage(chatID, "Нет данных по выбранному фильтру."))
		return
	}
	if len(filtered) > exportLimit {
		bot.Send(tgbotapi.NewMessage(chatID, fmt.Sprintf("Слишком большой экспорт! (>%d записей)", exportLimit)))
		return
	}

	f := excelize.NewFile()
	sheet := "Отчёт"
	f.SetSheetName("Sheet1", sheet)
	headers := []string{"Дата", "Время", "ФИО", "Действие", "Локация"}
	for i, h := range headers {
		cell, _ := excelize.CoordinatesToCellName(i+1, 1)
		f.SetCellValue(sheet, cell, h)
	}
	for idx, row := range filtered {
		if len(row) < 5 {
			for len(row) < 5 {
				row = append(row, "-")
			}
		}
		datetime := row[0]
		name := row[2]
		action := row[3]
		location := cleanLocation(row[4])
		date, timePart := splitDateTime(datetime)
		values := []string{date, timePart, name, action, location}
		for j, v := range values {
			cell, _ := excelize.CoordinatesToCellName(j+1, idx+2)
			f.SetCellValue(sheet, cell, v)
		}
		var style int
		if action == "Прибыл" {
			style, _ = f.NewStyle(`{"fill":{"type":"pattern","color":["#D8F6CE"],"pattern":1}}`)
		} else if action == "Убыл" {
			style, _ = f.NewStyle(`{"fill":{"type":"pattern","color":["#FFD6D6"],"pattern":1}}`)
		}
		f.SetCellStyle(sheet, fmt.Sprintf("A%d", idx+2), fmt.Sprintf("E%d", idx+2), style)
	}
	for col := 'A'; col <= 'E'; col++ {
		f.SetColWidth(sheet, string(col), string(col), 18)
	}
	filename := fmt.Sprintf("report_%d.xlsx", time.Now().Unix())
	err := f.SaveAs(filename)
	if err != nil {
		bot.Send(tgbotapi.NewMessage(chatID, "Ошибка создания Excel файла"))
		return
	}
	defer os.Remove(filename)
	excelFile, err := os.Open(filename)
	if err != nil {
		bot.Send(tgbotapi.NewMessage(chatID, "Ошибка отправки отчёта"))
		return
	}
	defer excelFile.Close()
	doc := tgbotapi.NewDocument(chatID, tgbotapi.FileReader{
		Name:   "Отчёт_Табель.xlsx",
		Reader: excelFile,
		Size:   -1,
	})
	doc.Caption = "📊 Отчёт по табелю"
	bot.Send(doc)
}

// --- Логика фильтров даты ---

func filterToday(row []string) bool {
	if len(row) == 0 {
		return false
	}
	today := time.Now().Format("02.01.2006")
	return strings.HasPrefix(row[0], today)
}
func filterYesterday(row []string) bool {
	if len(row) == 0 {
		return false
	}
	yesterday := time.Now().AddDate(0, 0, -1).Format("02.01.2006")
	return strings.HasPrefix(row[0], yesterday)
}
func filterLastNDays(n int) func([]string) bool {
	return func(row []string) bool {
		if len(row) == 0 {
			return false
		}
		layout := "02.01.2006 15:04:05"
		t, err := time.Parse(layout, row[0])
		if err != nil {
			return false
		}
		return t.After(time.Now().AddDate(0, 0, -n-1))
	}
}

// --- Чистка эмодзи для Excel ---

func cleanLocation(loc string) string {
	s := emojiRegex.ReplaceAllString(loc, "")
	return strings.TrimSpace(s)
}

// --- Поддержка меню локаций ---

func leaveMenu() tgbotapi.InlineKeyboardMarkup {
	rows := [][]tgbotapi.InlineKeyboardButton{}
	for i := 0; i < len(leaveLocations); i += 2 {
		row := []tgbotapi.InlineKeyboardButton{
			tgbotapi.NewInlineKeyboardButtonData(leaveLocations[i], leaveLocations[i]),
		}
		if i+1 < len(leaveLocations) {
			row = append(row, tgbotapi.NewInlineKeyboardButtonData(leaveLocations[i+1], leaveLocations[i+1]))
		}
		rows = append(rows, row)
	}
	return tgbotapi.NewInlineKeyboardMarkup(rows...)
}

// --- Сводка для админа ---

func adminSummary(bot *tgbotapi.BotAPI, chatID int64) {
	type OutUser struct {
		Name    string
		Location string
	}
	var inList, outList []string
	var outUsers []OutUser
	allUsers := getAllUserNames()
	for _, user := range allUsers {
		userID := getUserIDByName(user)
		if userID == "" {
			continue
		}
		action, loc := getLastActionStr(userID)
		cleanName := capitalizeName(user)
		if action == "Прибыл" {
			inList = append(inList, cleanName)
		} else if action == "Убыл" {
			outUsers = append(outUsers, OutUser{cleanName, cleanLocation(loc)})
		}
	}
	sort.Strings(inList)
	sort.Slice(outUsers, func(i, j int) bool {
		return outUsers[i].Name < outUsers[j].Name
	})
	var b strings.Builder
	b.WriteString(fmt.Sprintf("👥 В части (%d):\n", len(inList)))
	for _, name := range inList {
		b.WriteString("— " + name + "\n")
	}
	if len(outUsers) > 0 {
		b.WriteString(fmt.Sprintf("\n🚶 Вне части (%d):\n", len(outUsers)))
		for _, ou := range outUsers {
			b.WriteString(fmt.Sprintf("— %s (%s)\n", ou.Name, ou.Location))
		}
	}
	bot.Send(tgbotapi.NewMessage(chatID, b.String()))
}

func getAllUserNames() []string {
	rows := readCSV(usersFile)
	var names []string
	for _, row := range rows {
		if len(row) > 1 {
			names = append(names, row[1])
		}
	}
	return names
}
func getUserIDByName(name string) string {
	rows := readCSV(usersFile)
	for _, row := range rows {
		if len(row) > 1 && row[1] == name {
			return row[0]
		}
	}
	return ""
}
func getLastActionStr(userID string) (action, location string) {
	rows := readCSV(dataFile)
	for i := len(rows) - 1; i >= 0; i-- {
		if len(rows[i]) > 1 && rows[i][1] == userID {
			return rows[i][3], rows[i][4]
		}
	}
	return "", ""
}
func capitalizeName(s string) string {
	if len(s) == 0 {
		return s
	}
	return strings.ToUpper(string([]rune(s)[0])) + s[1:]
}

// --- Проверки и валидации ---

func isUserRegistered(userID int) bool {
	idStr := strconv.Itoa(userID)
	rows := readCSV(usersFile)
	for _, row := range rows {
		if len(row) > 0 && row[0] == idStr {
			return true
		}
	}
	return false
}
func isValidName(name string) bool {
	if len(name) < 5 || !strings.Contains(name, " ") || !strings.Contains(name, ".") {
		return false
	}
	parts := strings.Fields(name)
	if len(parts) != 2 {
		return false
	}
	initials := parts[1]
	if len(initials) != 4 || initials[1] != '.' || initials[3] != '.' {
		return false
	}
	return true
}
func getUserName(userID int, u *tgbotapi.User) string {
	idStr := strconv.Itoa(userID)
	rows := readCSV(usersFile)
	for _, row := range rows {
		if len(row) > 1 && row[0] == idStr {
			return row[1]
		}
	}
	if u != nil {
		return fmt.Sprintf("%s %s.%s.", u.LastName, string([]rune(u.FirstName)[0]), string([]rune(u.UserName)[0]))
	}
	return "Неизвестно"
}
func saveUserName(userID int, name string, chatID int64) {
	rows := readCSV(usersFile)
	idStr := strconv.Itoa(userID)
	found := false
	for i, row := range rows {
		if len(row) > 0 && row[0] == idStr {
			rows[i][1] = name
			found = true
			break
		}
	}
	if !found {
		rows = append(rows, []string{idStr, name, strconv.FormatInt(chatID, 10)})
	}
	writeCSV(usersFile, rows)
}
func getLastAction(userID int) (action, location string) {
	rows := readCSV(dataFile)
	idStr := strconv.Itoa(userID)
	for i := len(rows) - 1; i >= 0; i-- {
		if len(rows[i]) > 1 && rows[i][1] == idStr {
			return rows[i][3], rows[i][4]
		}
	}
	return "", ""
}
func getLastActions(userID string, n int) [][]string {
	rows := readCSV(dataFile)
	var filtered [][]string
	for i := len(rows) - 1; i >= 0; i-- {
		if len(rows[i]) > 1 && rows[i][1] == userID {
			filtered = append(filtered, rows[i])
			if len(filtered) >= n {
				break
			}
		}
	}
	for i, j := 0, len(filtered)-1; i < j; i, j = i+1, j-1 {
		filtered[i], filtered[j] = filtered[j], filtered[i]
	}
	return filtered
}
func splitDateTime(dt string) (string, string) {
	parts := strings.SplitN(dt, " ", 2)
	if len(parts) == 2 {
		return parts[0], parts[1]
	}
	return dt, ""
}

// --- CSV-файлы ---

func readCSV(filename string) [][]string {
	file, err := os.OpenFile(filename, os.O_RDONLY|os.O_CREATE, 0644)
	if err != nil {
		return [][]string{}
	}
	defer file.Close()
	reader := csv.NewReader(file)
	rows, _ := reader.ReadAll()
	return rows
}
func writeCSV(filename string, rows [][]string) {
	file, err := os.OpenFile(filename, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return
	}
	defer file.Close()
	writer := csv.NewWriter(file)
	writer.WriteAll(rows)
	writer.Flush()
}

// --- Логика админов/прав ---

func isRootAdmin(userID int) bool {
	return int64(userID) == adminRootID
}
func isAdminAny(userID int) bool {
	if isRootAdmin(userID) {
		return true
	}
	idStr := strconv.Itoa(userID)
	rows := readCSV(adminsFile)
	for _, row := range rows {
		if len(row) > 1 && row[0] == idStr {
			return true
		}
	}
	return false
}
func isAdminWithRight(userID int, code string) bool {
	if isRootAdmin(userID) {
		return true
	}
	idStr := strconv.Itoa(userID)
	rows := readCSV(adminsFile)
	for _, row := range rows {
		if len(row) > 2 && row[0] == idStr {
			for i, r := range adminRights {
				if r.Code == code && len(row) > i+2 && row[i+2] == "1" {
					return true
				}
			}
		}
	}
	return false
}
func getAdmins() []Admin {
	rows := readCSV(adminsFile)
	var admins []Admin
	for _, row := range rows {
		if len(row) >= 3 {
			id, _ := strconv.Atoi(row[0])
			name := row[1]
			rights := make(map[string]bool)
			for i, r := range adminRights {
				if len(row) > i+2 && row[i+2] == "1" {
					rights[r.Code] = true
				}
			}
			admins = append(admins, Admin{ID: id, Name: name, Rights: rights})
		}
	}
	return admins
}
func getSortedUsers() []User {
	rows := readCSV(usersFile)
	var users []User
	for _, row := range rows {
		if len(row) >= 3 {
			uid, _ := strconv.Atoi(row[0])
			name := capitalizeName(row[1])
			cid, _ := strconv.ParseInt(row[2], 10, 64)
			users = append(users, User{ID: uid, Name: name, ChatID: cid})
		}
	}
	sort.Slice(users, func(i, j int) bool {
		return users[i].Name < users[j].Name
	})
	return users
}
func getAdminRights(userID int) map[string]bool {
	idStr := strconv.Itoa(userID)
	rows := readCSV(adminsFile)
	for _, row := range rows {
		if len(row) > 1 && row[0] == idStr {
			rights := make(map[string]bool)
			for i, r := range adminRights {
				if len(row) > i+2 && row[i+2] == "1" {
					rights[r.Code] = true
				}
			}
			return rights
		}
	}
	return make(map[string]bool)
}
func saveAdminRights(userID int, name string, rights map[string]bool) {
	rows := readCSV(adminsFile)
	idStr := strconv.Itoa(userID)
	newRow := []string{idStr, name}
	for _, r := range adminRights {
		if rights[r.Code] {
			newRow = append(newRow, "1")
		} else {
			newRow = append(newRow, "0")
		}
	}
	found := false
	for i, row := range rows {
		if len(row) > 0 && row[0] == idStr {
			rows[i] = newRow
			found = true
			break
		}
	}
	if !found {
		rows = append(rows, newRow)
	}
	writeCSV(adminsFile, rows)
}

// --- Сохранение и уведомление ---

func saveAttendance(dt, uid, name, action, location string) {
	rows := readCSV(dataFile)
	rows = append(rows, []string{dt, uid, name, action, location})
	writeCSV(dataFile, rows)
}

// Уведомление главному админу о каждой отметке
func notifyAdminAboutMark(bot *tgbotapi.BotAPI, userID int, fio string, action string, location string, datetime string) {
	adminID := int64(adminRootID)
	var emoji, locationLine string
	if action == "Прибыл" {
		emoji = "🟢"
		locationLine = "📍 Локация: -"
	} else {
		emoji = "🔴"
		locationLine = fmt.Sprintf("📍 Локация: %s", cleanLocation(location))
	}
	txt := fmt.Sprintf(
		"📋 <b>Новая отметка</b>\n"+
			"👤 <b>ФИО:</b> %s\n"+
			"🆔 <b>ID:</b> %d\n"+
			"⏰ <b>Время:</b> %s\n"+
			"⚡ <b>Действие:</b> %s %s\n"+
			"%s",
		fio, userID, datetime, emoji, action, locationLine)
	msg := tgbotapi.NewMessage(adminID, txt)
	msg.ParseMode = "HTML"
	bot.Send(msg)
}

// --- Ежедневные автонапоминания ---

func reminderScheduler(bot *tgbotapi.BotAPI) {
	for {
		now := time.Now()
		next := time.Date(now.Year(), now.Month(), now.Day(), reminderHour, reminderMinute, 0, 0, now.Location())
		if now.After(next) {
			next = next.Add(24 * time.Hour)
		}
		time.Sleep(time.Until(next))
		sendReminders(bot)
	}
}
func sendReminders(bot *tgbotapi.BotAPI) {
	users := getSortedUsers()
	for _, u := range users {
		lastStatus, _ := getLastAction(u.ID)
		if lastStatus == "Убыл" {
			txt := reminderTexts[randText.Intn(len(reminderTexts))]
			msg := tgbotapi.NewMessage(u.ChatID, txt)
			bot.Send(msg)
		}
	}
}

// --- Ежедневная сводка для командира (19:00) ---

func dailyReportScheduler(bot *tgbotapi.BotAPI) {
	for {
		now := time.Now()
		next := time.Date(now.Year(), now.Month(), now.Day(), reportHour, 0, 0, 0, now.Location())
		if now.After(next) {
			next = next.Add(24 * time.Hour)
		}
		time.Sleep(time.Until(next))
		adminSummary(bot, int64(adminRootID))
	}
}

// --- Конец main.go ---
