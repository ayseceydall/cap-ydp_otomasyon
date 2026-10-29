# ÇAP/YDP Öğrenci Takip Otomasyonu

## Proje Hakkında

Bu projeyi, bölümümüzdeki çift anadal (ÇAP) ve yandal (YDP) öğrencilerinin ders, not ve belge süreçlerini daha kolay takip edebilmek için geliştirdim.

Şu anda bu işlemlerin bir kısmı formlar ve kâğıtlar üzerinden yürütüldüğü için öğrenci bilgilerinin tek bir yerde tutulmasını ve gerektiğinde kolayca görüntülenmesini amaçladım. Sistem üzerinden öğrencilerin ders durumları, belgeleri ve akademik ilerlemeleri takip edilebiliyor. Ayrıca öğrenci ile koordinatör arasında mesajlaşma da yapılabiliyor.

## Canlı Uygulama

Uygulamayı aşağıdaki bağlantıdan ziyaret edebilirsiniz:

https://cap-ydp-otomasyon-6eoy.onrender.com/

## Kullandığım Teknolojiler

Projeyi geliştirirken şu teknolojilerden yararlandım:

- **Python ve Django:** Uygulamanın temel yapısı ve sunucu tarafı
- **HTML ve CSS:** Sayfaların tasarımı
- **Veritabanı:** Öğrenci, ders, not ve mesaj kayıtlarının tutulması
- **Supabase Storage:** Yüklenen belgelerin saklanması
- **Render:** Uygulamanın internette yayımlanması
- **Git ve GitHub:** Kodların saklanması ve yapılan değişikliklerin takibi

## Kullanıcı Rolleri

Sistemde üç farklı kullanıcı rolü bulunuyor.

**Koordinatör:** Öğrenci ekleme, ders ve not kayıtlarını inceleme, belgeleri değerlendirme ve öğrencilerin akademik durumlarını takip etme işlemlerini yapar.

**Öğrenci:** Kendi bilgilerini ve ders durumunu görüntüleyebilir, belge yükleyebilir ve koordinatörle mesajlaşabilir.

**Bölüm başkanı:** Öğrenci kayıtlarını ve işlem geçmişini incelemek için sistemi kullanır. Kayıtları değiştirmeden görüntüleme yetkisine sahip olacak şekilde tasarlanmıştır.

## Uygulamadaki Özellikler

Projenin şu ana kadar geliştirdiğim bölümlerinde şu özellikler bulunuyor:

- Öğrenci bilgilerinin eklenmesi ve yönetilmesi
- Ders kataloğu ve öğrencilerin ders kayıtlarının takip edilmesi
- Ders ve not kayıtlarının onay süreçleri
- GANO bilgilerinin kaydedilmesi
- Geçmiş dönem ders kayıtlarının tutulması
- Öğrencilerin belge yükleyebilmesi ve belgelerin indirilebilmesi
- Belgelerin eski sürümlerinin korunması
- Öğrenci ve koordinatör arasında mesajlaşma
- Mesajlara PDF veya görsel eklenebilmesi
- Okunmamış mesaj sayısının gösterilmesi
- Tamamlanan ve kalan derslerin, kredi ve AKTS bilgilerinin görüntülenmesi
- Akademik kural sürümlerinin yönetim panelinden oluşturulması
- Önemli işlemlerin geçmiş kaydının tutulması

## Akademik İlerleme

Akademik ilerleme ekranında öğrencinin zorunlu dersleri, ders denemeleri, tamamladığı dersler ve kalan kredi/AKTS miktarları gösterilir.

Aynı ders birden fazla kez alınmışsa denemeler ayrı ayrı görüntülenebilir. Hesaplamalarda koordinatör tarafından onaylanmış kayıtlar dikkate alınır.

Yönergelerdeki tüm kuralların otomatik hesaplamalara uygulanması ise geliştirmeye ve test edilmeye devam eden konulardan biridir.

## Kurulum

Projeyi kendi bilgisayarında çalıştırmak için Python ve gerekli bağımlılıkların yüklü olması gerekir.

Önce GitHub deposunu indir:

```bash
git clone https://github.com/ayseceydall/cap-ydp_otomasyon
cd cap_ydp_otomasyon
```

Ardından sanal ortam oluşturup etkinleştir:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Gerekli kütüphaneleri yükle:

```bash
pip install -r requirements.txt
```

Ortam değişkenlerini ve veritabanı bağlantısını ayarladıktan sonra migration işlemlerini çalıştır:

```bash
python manage.py migrate
```

Son olarak uygulamayı başlat:

```bash
python manage.py runserver
```

Uygulama varsayılan olarak `http://127.0.0.1:8000/` adresinde açılır.

## Test ve Güvenlik

Geliştirme sırasında gerçek öğrenci bilgileri yerine sentetik test verileri kullandım.

Öğrenci, koordinatör ve bölüm başkanı hesaplarıyla temel erişim kontrollerini yaptım. Başka bir öğrenciye ait özel belgeye erişmeye çalışıldığında erişimin engellendiğini de test ettim.

Belge yükleme ve indirme, mesajlaşma, mesaj ekleri ve akademik ilerleme ekranı canlı ortamda denendi. Bunun yanında, kapsamlı güvenlik testleri ve akademik yönerge kurallarının tamamının otomatik uygulanması üzerinde geliştirme yapılması gerekiyor.

## Projenin Mevcut Durumu

Projenin temel özelliklerini geliştirerek canlı ortamda çalışır hâle getirdim. Öğrenci yönetimi, belge işlemleri, mesajlaşma ve akademik ilerleme gibi bölümlerin önemli bir kısmını test ettim.

Bazı ayrıntılı akademik ve idari işlemlerin geliştirilmesi ve doğrulanması devam ediyor. Bu nedenle proje şu an temel işlevleri çalışan, geliştirilmeye açık bir uygulama durumunda.

## Veri Gizliliği

Testlerde yalnızca sentetik veriler kullanılmalıdır. Gerçek öğrenci bilgileri, kişisel belgeler, kullanıcı parolaları ve gizli bağlantı anahtarları kaynak kod deposuna eklenmemelidir.
