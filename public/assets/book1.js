// Book 1 course data. Used by book-1.html (lesson list) and lesson.html (lesson page).
// Titles come from materials/book1/LESSON-MAP.md.
//
// For each lesson:
//   video: paste the video's EMBED address when it is recorded, e.g.
//          "https://player.vimeo.com/video/123456789" or "https://www.youtube.com/embed/abc123".
//          Leave "" and the page says the video is coming soon.
//   free:  true lets anyone watch. Other lessons show the "join the course" message.
var BOOK1 = {
  title: "Book 1",
  minutes: 40,
  parts: [
    { name: "Getting ready and the vowels", from: 1, to: 4 },
    { name: "First sounds: m b c l n", from: 5, to: 10 },
    { name: "More sounds: g f s d w", from: 11, to: 16 },
    { name: "Reading words: z k t y q", from: 17, to: 23 },
    { name: "The sound v and the cattle kraal", from: 24, to: 26 },
    { name: "Last sounds and stories", from: 27, to: 35 }
  ],
  lessons: [
    { n: 1, nd: "Imuli yami", en: "My family", type: "Getting ready", culture: "Respect for elders", video: "", free: true },
    { n: 2, nd: "Imisebenzi yasekhaya", en: "Work at home", type: "Getting ready", culture: "Helping at home", video: "", free: true },
    { n: 3, nd: "Onkamisa: a e i o u", en: "Meet the vowels", type: "Vowels", culture: "Two hands", video: "", free: false },
    { n: 4, nd: "Onkamisa: sidlala", en: "Playing with the vowels", type: "Vowels", culture: "Our language", video: "", free: false },
    { n: 5, nd: "Umsindo m", en: "The sound m", type: "New sound", culture: "Our mothers", video: "", free: false },
    { n: 6, nd: "Umsindo b", en: "The sound b", type: "New sound", culture: "Our fathers", video: "", free: false },
    { n: 7, nd: "Umsindo c", en: "The click c", type: "New sound", culture: "Mopane worms", video: "", free: false },
    { n: 8, nd: "Umsindo l", en: "The sound l", type: "New sound", culture: "Fishing", video: "", free: false },
    { n: 9, nd: "Umsindo n", en: "The sound n", type: "New sound", culture: "Farm animals", video: "", free: false },
    { n: 10, nd: "Siyabuyekeza 1", en: "Review: m b c l n", type: "Review", culture: "Well done!", video: "", free: false },
    { n: 11, nd: "Umsindo g", en: "The sound g", type: "New sound", culture: "Folktales", video: "", free: false },
    { n: 12, nd: "Umsindo f", en: "The sound f", type: "New sound", culture: "Body song", video: "", free: false },
    { n: 13, nd: "Umsindo s", en: "The sound s", type: "New sound", culture: "Two goodbyes", video: "", free: false },
    { n: 14, nd: "Umsindo d", en: "The sound d", type: "New sound", culture: "Okra", video: "", free: false },
    { n: 15, nd: "Umsindo w", en: "The sound w", type: "New sound", culture: "Keeping clean", video: "", free: false },
    { n: 16, nd: "Siyabuyekeza 2", en: "Review: g f s d w", type: "Review", culture: "Great work!", video: "", free: false },
    { n: 17, nd: "Umsindo z", en: "The sound z", type: "New sound", culture: "Children of the sky", video: "", free: false },
    { n: 18, nd: "Umsindo k", en: "The sound k", type: "New sound", culture: "The homestead", video: "", free: false },
    { n: 19, nd: "Bala amabala", en: "Reading words: z and k", type: "Reading", culture: "The river spirit", video: "", free: false },
    { n: 20, nd: "Umsindo t", en: "The sound t", type: "New sound", culture: "Bulawayo and the railway", video: "", free: false },
    { n: 21, nd: "Umsindo y", en: "The sound y", type: "New sound", culture: "Herding cattle", video: "", free: false },
    { n: 22, nd: "Umsindo q", en: "The click q", type: "New sound", culture: "Sorghum", video: "", free: false },
    { n: 23, nd: "Siyabuyekeza 3", en: "Review: z k t y q + capital letters", type: "Review", culture: "Sour milk", video: "", free: false },
    { n: 24, nd: "Umsindo v", en: "The sound v", type: "New sound", culture: "The vuvuzela", video: "", free: false },
    { n: 25, nd: "Esibayeni", en: "At the cattle kraal", type: "Reading", culture: "The cattle kraal", video: "", free: false },
    { n: 26, nd: "Siyabuyekeza 4", en: "Review: finish the words", type: "Review", culture: "We’re over halfway!", video: "", free: false },
    { n: 27, nd: "Umsindo j", en: "The sound j", type: "New sound", culture: "The city", video: "", free: false },
    { n: 28, nd: "Umsindo x", en: "The click x", type: "New sound", culture: "Three clicks", video: "", free: false },
    { n: 29, nd: "Imisindo h lo p", en: "The sounds h and p", type: "New sound", culture: "We all help", video: "", free: false },
    { n: 30, nd: "Gezisa imiganu", en: "Wash the dishes", type: "Reading", culture: "Wooden dishes", video: "", free: false },
    { n: 31, nd: "Umabonakude", en: "The television", type: "Reading", culture: "One and many", video: "", free: false },
    { n: 32, nd: "Ezokuhamba", en: "Getting around", type: "Reading", culture: "By bus", video: "", free: false },
    { n: 33, nd: "Izulu", en: "The weather", type: "Reading", culture: "Winter and summer", video: "", free: false },
    { n: 34, nd: "Umhlaba wethu", en: "Caring for our land", type: "Reading", culture: "The forest", video: "", free: false },
    { n: 35, nd: "Umbukiso wemuli", en: "Book 1 family show", type: "Show", culture: "Very well done!", video: "", free: false }
  ]
};
